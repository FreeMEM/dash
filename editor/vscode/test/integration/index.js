// Tests inside a real VS Code (npm run test:vscode): the installed `code` runs them with this folder
// as the extension under development, in a profile of its own. They write their result to the file in
// DASH_IT_RESULT (VS Code's window has no console we can read) and close the window.
const vscode = require('vscode');
const assert = require('assert');
const fs = require('fs');

const results = [];
async function check(name, fn) {
    try { await fn(); results.push('ok   ' + name); } catch (e) { results.push('FAIL ' + name + ': ' + (e && e.message)); }
}

async function typeLines(editor, text) {
    for (const ch of text) {
        if (ch === '\n') await vscode.commands.executeCommand('dash.newline');
        else await vscode.commands.executeCommand('type', { text: ch });
    }
}

async function run() {
    await check('Enter after "func" adds the end, cursor inside', async () => {
        const doc = await vscode.workspace.openTextDocument({ language: 'dash', content: '' });
        const editor = await vscode.window.showTextDocument(doc);
        await typeLines(editor, 'func suma(a, b)\nreturn a + b');
        assert.strictEqual(doc.getText(), 'func suma(a, b)\n    return a + b\nend');
    });
    await check('Enter inside a block that has its end: no second end', async () => {
        const doc = await vscode.workspace.openTextDocument({ language: 'dash', content: 'Main\n    x = 1\nend' });
        const editor = await vscode.window.showTextDocument(doc);
        editor.selection = new vscode.Selection(0, 4, 0, 4);
        await vscode.commands.executeCommand('dash.newline');
        assert.strictEqual(doc.getText(), 'Main\n    \n    x = 1\nend');
    });
    await check('nested: if inside Main', async () => {
        const doc = await vscode.workspace.openTextDocument({ language: 'dash', content: '' });
        const editor = await vscode.window.showTextDocument(doc);
        await typeLines(editor, 'Main\nif x > 1\nPrint x');
        assert.strictEqual(doc.getText(), 'Main\n    if x > 1\n        Print x\n    end\nend');
    });
    await check('else goes back to the level of its if', async () => {
        const doc = await vscode.workspace.openTextDocument({ language: 'dash', content: '' });
        const editor = await vscode.window.showTextDocument(doc);
        await typeLines(editor, 'if a\nb = 1\nelse');
        await new Promise((r) => setTimeout(r, 300));   // the outdent is an edit of its own, after the typing
        assert.strictEqual(doc.getText(), 'if a\n    b = 1\nelse\nend');
    });
    await check('one undo takes the Enter and its end away', async () => {
        const doc = await vscode.workspace.openTextDocument({ language: 'dash', content: 'while x' });
        const editor = await vscode.window.showTextDocument(doc);
        editor.selection = new vscode.Selection(0, 7, 0, 7);
        await vscode.commands.executeCommand('dash.newline');
        assert.strictEqual(doc.getText(), 'while x\n    \nend');
        await vscode.commands.executeCommand('undo');
        assert.strictEqual(doc.getText(), 'while x');
    });
    await check('snippets are there', async () => {
        const doc = await vscode.workspace.openTextDocument({ language: 'dash', content: '' });
        await vscode.window.showTextDocument(doc);
        await vscode.commands.executeCommand('editor.action.insertSnippet', { langId: 'dash', name: 'while' });
        assert.match(doc.getText(), /^while condicion\n {4}\nend$/);
    });
    await check('language server: an error shows while typing, and goes when fixed', async () => {
        const path = require('path');
        const os = require('os');
        const repo = path.resolve(__dirname, '..', '..', '..', '..');
        await vscode.workspace.getConfiguration('dash').update('path', repo, vscode.ConfigurationTarget.Global);
        const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'dash_it_'));
        const file = path.join(dir, 'prueba.dash');
        fs.writeFileSync(file, 'Main\n    x = 1\n    Print x + nada\nend\n');
        const doc = await vscode.workspace.openTextDocument(file);
        const editor = await vscode.window.showTextDocument(doc);
        const until = async (cond) => {
            for (let i = 0; i < 150; i++) {
                if (cond(vscode.languages.getDiagnostics(doc.uri))) return vscode.languages.getDiagnostics(doc.uri);
                await new Promise((r) => setTimeout(r, 100));
            }
            throw new Error('timed out; diagnostics: ' + JSON.stringify(vscode.languages.getDiagnostics(doc.uri)));
        };
        const [d] = await until((ds) => ds.length > 0);
        assert.match(d.message, /nada/);
        assert.strictEqual(d.range.start.line, 2);
        assert.strictEqual(d.range.start.character, 14);
        await editor.edit((e) => e.replace(new vscode.Range(2, 14, 2, 18), '2'));
        await until((ds) => ds.length === 0);
        fs.rmSync(dir, { recursive: true, force: true });
    });
    fs.writeFileSync(process.env.DASH_IT_RESULT, results.join('\n') + '\n');
    await vscode.commands.executeCommand('workbench.action.closeWindow');
}

module.exports = { run };
