// @ts-check
// "end" by itself: Enter at the end of a line that opens a block (func, if, while, struct, Main...) adds
// the "end" under it when the block has none yet, as Ruby's endwise does. Plain functions over the lines
// of the document (tested without VS Code) and the command bound to Enter in .dash files.

// a line that opens a block closed by "end"; elif/else only go on one
const OPENER = /^\s*(?:(?:@native(?:\s*\(\s*borrow\s*\))?\s+)?func\b|if\b|while\b|for\b|struct\b|enum\b|Window\b|Main\b|EventLoop\b|On\b|@c\b)/;
const CONTINUES = /^\s*(?:elif|else)\b/;
const END = /^\s*end\b/;

/** @param {string} line */
const indentOf = (line) => (/^\s*/.exec(line) || [''])[0];
/** @param {string} line */
const blank = (line) => /^\s*(#.*)?$/.test(line);

/**
 * Does the block opened at lines[row] still lack its "end"?
 * @param {string[]} lines
 * @param {number} row
 */
function needsEnd(lines, row) {
    const line = lines[row];
    if (!OPENER.test(line) || /\bend\s*(#.*)?$/.test(line)) return false;   // "enum E A, B end" on one line
    // "@extern(...)" then "func f(...)": a declaration, with no body and no end
    for (let i = row - 1; i >= 0; i--) {
        if (blank(lines[i])) continue;
        if (/^\s*@extern\b/.test(lines[i])) return false;
        break;
    }
    // the first line after the block that is not deeper: its "end" (or elif/else of an if) closes it
    const indent = indentOf(line).length;
    for (let i = row + 1; i < lines.length; i++) {
        if (blank(lines[i])) continue;
        const n = indentOf(lines[i]).length;
        if (n > indent) continue;
        if (n === indent && (END.test(lines[i]) || CONTINUES.test(lines[i]))) return false;
        return true;
    }
    return true;
}

/**
 * The Enter of .dash files: the usual newline, then the "end" if the line just left opens a block without one.
 * @param {typeof import('vscode')} vscode
 */
async function newline(vscode) {
    const editor = vscode.window.activeTextEditor;
    const auto = vscode.workspace.getConfiguration('dash.editor').get('autoEnd') !== false;
    if (editor && auto && editor.selections.length === 1 && editor.selection.isEmpty) {
        const doc = editor.document;
        const here = editor.selection.active;
        const lines = [];
        for (let i = 0; i < doc.lineCount; i++) lines.push(doc.lineAt(i).text);
        if (here.character === lines[here.line].length && needsEnd(lines, here.line)) {
            // all in one edit (one undo): the new line one step deeper than the block, and the "end".
            // (Done with VS Code's Enter, it took away the indentation it had put as soon as the "end"
            // came after, editor.trimAutoWhitespace, and indented like the "end" if it came before.)
            const indent = indentOf(lines[here.line]);
            const step = editor.options.insertSpaces === false ? '\t' : ' '.repeat(Number(editor.options.tabSize) || 4);
            await editor.edit((e) => e.insert(here, '\n' + indent + step + '\n' + indent + 'end'));
            const pos = new vscode.Position(here.line + 1, (indent + step).length);
            editor.selection = new vscode.Selection(pos, pos);
            return;
        }
    }
    await vscode.commands.executeCommand('type', { text: '\n' });
}

// a line that is only "else", "elif ..." or "end" goes back to the level of its block
const OUTDENTS = /^\s*(?:else|end|elif\b.*)\s*$/;

/**
 * The indentation lines[row] should have now that it reads else/elif/end, or null to leave it:
 * one step less than the line above (or the same, if the line above opens the block).
 * @param {string[]} lines
 * @param {number} row
 * @param {string} step
 */
function outdentFor(lines, row, step) {
    if (!OUTDENTS.test(lines[row])) return null;
    let prev = row - 1;
    while (prev >= 0 && blank(lines[prev])) prev--;
    if (prev < 0) return null;
    const above = indentOf(lines[prev]);
    const mine = indentOf(lines[row]);
    if (mine !== above) return null;                      // already where the user wants it
    if (OPENER.test(lines[prev]) || CONTINUES.test(lines[prev])) return null;   // empty block: same level
    return above.endsWith(step) ? above.slice(0, above.length - step.length) : null;
}

/**
 * After a letter typed in a .dash file: else/elif/end back to its level (VS Code's own indentation rules
 * do it only sometimes: not with an "end" below, the usual case with the end put by newline).
 * @param {typeof import('vscode')} vscode
 * @param {import('vscode').TextDocumentChangeEvent} event
 */
async function onTyped(vscode, event) {
    const editor = vscode.window.activeTextEditor;
    if (!editor || editor.document !== event.document || event.document.languageId !== 'dash') return;
    if (event.reason !== undefined || event.contentChanges.length !== 1) return;     // undo, redo, several
    const change = event.contentChanges[0];
    if (!/^[a-z]$/.test(change.text) || !change.range.isEmpty) return;
    const doc = event.document;
    const row = change.range.start.line;
    const lines = [];
    for (let i = Math.max(0, row - 400); i <= row; i++) lines.push(doc.lineAt(i).text);
    const step = editor.options.insertSpaces === false ? '\t' : ' '.repeat(Number(editor.options.tabSize) || 4);
    const want = outdentFor(lines, lines.length - 1, step);
    if (want === null) return;
    const old = indentOf(lines[lines.length - 1]);
    await editor.edit((e) => e.replace(new vscode.Range(row, 0, row, old.length), want),
                      { undoStopBefore: false, undoStopAfter: false });
}

module.exports = { needsEnd, newline, outdentFor, onTyped };
