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

// Typing (the "type" command) only reaches the editor when VS Code's window has the focus of the desktop:
// when it does not get it (the user is typing in another window), the tests that type are skipped
let canType = null;
async function typingWorks() {
    if (canType !== null) return canType;
    const doc = await vscode.workspace.openTextDocument({ language: 'dash', content: '' });
    await vscode.window.showTextDocument(doc);
    for (let i = 0; i < 30 && !doc.getText(); i++) {
        await vscode.commands.executeCommand('type', { text: 'x' });
        if (!doc.getText()) await new Promise((r) => setTimeout(r, 100));
    }
    canType = doc.getText() !== '';
    await vscode.commands.executeCommand('workbench.action.revertAndCloseActiveEditor');
    return canType;
}

async function checkTyping(name, fn) {
    if (!(await typingWorks())) { results.push('SKIP ' + name + ' (la ventana no tiene el foco del escritorio)'); return; }
    return check(name, fn);
}

async function typeLines(editor, text) {
    for (const ch of text) {
        if (ch === '\n') await vscode.commands.executeCommand('dash.newline');
        else await vscode.commands.executeCommand('type', { text: ch });
    }
}

async function run() {
    const ext = vscode.extensions.all.find((e) => e.packageJSON && e.packageJSON.name === 'dash-mui-editor');
    try {
        await ext.activate();
    } catch (e) {
        results.push('FAIL activation: ' + (e && e.stack));
    }
    await checkTyping('Enter after "func" adds the end, cursor inside', async () => {
        const doc = await vscode.workspace.openTextDocument({ language: 'dash', content: '' });
        const editor = await vscode.window.showTextDocument(doc);
        await typeLines(editor, 'func suma(a, b)\nreturn a + b');
        assert.strictEqual(doc.getText(), 'func suma(a, b)\n    return a + b\nend');
    });
    await checkTyping('Enter inside a block that has its end: no second end', async () => {
        const doc = await vscode.workspace.openTextDocument({ language: 'dash', content: 'Main\n    x = 1\nend' });
        const editor = await vscode.window.showTextDocument(doc);
        editor.selection = new vscode.Selection(0, 4, 0, 4);
        await vscode.commands.executeCommand('dash.newline');
        assert.strictEqual(doc.getText(), 'Main\n    \n    x = 1\nend');
    });
    await checkTyping('nested: if inside Main', async () => {
        const doc = await vscode.workspace.openTextDocument({ language: 'dash', content: '' });
        const editor = await vscode.window.showTextDocument(doc);
        await typeLines(editor, 'Main\nif x > 1\nPrint x');
        assert.strictEqual(doc.getText(), 'Main\n    if x > 1\n        Print x\n    end\nend');
    });
    await checkTyping('else goes back to the level of its if', async () => {
        const doc = await vscode.workspace.openTextDocument({ language: 'dash', content: '' });
        const editor = await vscode.window.showTextDocument(doc);
        await typeLines(editor, 'if a\nb = 1\nelse');
        await new Promise((r) => setTimeout(r, 300));   // the outdent is an edit of its own, after the typing
        assert.strictEqual(doc.getText(), 'if a\n    b = 1\nelse\nend');
    });
    await checkTyping('one undo takes the Enter and its end away', async () => {
        const doc = await vscode.workspace.openTextDocument({ language: 'dash', content: 'while x' });
        const editor = await vscode.window.showTextDocument(doc);
        editor.selection = new vscode.Selection(0, 7, 0, 7);
        await vscode.commands.executeCommand('dash.newline');
        assert.strictEqual(doc.getText(), 'while x\n    \nend');
        await vscode.commands.executeCommand('undo');
        assert.strictEqual(doc.getText(), 'while x');
    });
    await checkTyping('snippets are there', async () => {
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
    await check('language server: completion and signature help', async () => {
        const path = require('path');
        const os = require('os');
        const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'dash_it_'));
        const file = path.join(dir, 'completa.dash');
        fs.writeFileSync(file, 'struct Punto\n    x: Int = 0\nend\nMain\n    p = Punto(1)\n    Print p.x\nend\n');
        const doc = await vscode.workspace.openTextDocument(file);
        const editor = await vscode.window.showTextDocument(doc);
        let items = [];
        for (let i = 0; i < 150; i++) {          // the server has to analyze it once first
            const list = await vscode.commands.executeCommand('vscode.executeCompletionItemProvider', doc.uri,
                                                              new vscode.Position(5, 12));
            items = list.items.map((it) => (typeof it.label === 'string' ? it.label : it.label.label));
            if (items.includes('x')) break;
            await new Promise((r) => setTimeout(r, 100));
        }
        assert(items.includes('x'), 'members of p: ' + items.slice(0, 20).join(','));
        await editor.edit((e) => e.insert(new vscode.Position(5, 13), '\n    mui_text('));
        const help = await vscode.commands.executeCommand('vscode.executeSignatureHelpProvider', doc.uri,
                                                          new vscode.Position(6, 13));
        assert(help && help.signatures[0].label.startsWith('mui_text(text)'), JSON.stringify(help));
        fs.rmSync(dir, { recursive: true, force: true });
    });
    await check('language server: hover and go to definition', async () => {
        const path = require('path');
        const os = require('os');
        const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'dash_it_'));
        const file = path.join(dir, 'navega.dash');
        fs.writeFileSync(file, 'func doble(n: Int) -> Int\n    return n * 2\nend\nMain\n    Print doble(3)\nend\n');
        const doc = await vscode.workspace.openTextDocument(file);
        await vscode.window.showTextDocument(doc);
        let hovers = [];
        for (let i = 0; i < 150 && !hovers.length; i++) {
            hovers = await vscode.commands.executeCommand('vscode.executeHoverProvider', doc.uri, new vscode.Position(4, 12));
            if (!hovers.length) await new Promise((r) => setTimeout(r, 100));
        }
        const text = hovers.map((h) => h.contents.map((c) => c.value || c).join(' ')).join(' ');
        assert.match(text, /doble\(n: Int\) -> Int/);
        const defs = await vscode.commands.executeCommand('vscode.executeDefinitionProvider', doc.uri, new vscode.Position(4, 12));
        const d = defs[0];
        const range = d.range || d.targetRange;
        assert.strictEqual(range.start.line, 0);
        assert.strictEqual(range.start.character, 5);
        fs.rmSync(dir, { recursive: true, force: true });
    });
    await check('language server: outline and rename', async () => {
        const path = require('path');
        const os = require('os');
        const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'dash_it_'));
        const file = path.join(dir, 'esquema.dash');
        fs.writeFileSync(file, 'struct P\n    x: Int = 0\nend\nfunc doble(n: Int) -> Int\n    return n * 2\nend\nMain\n    Print doble(3)\nend\n');
        const doc = await vscode.workspace.openTextDocument(file);
        await vscode.window.showTextDocument(doc);
        let symbols = [];
        for (let i = 0; i < 150 && !symbols.length; i++) {
            symbols = (await vscode.commands.executeCommand('vscode.executeDocumentSymbolProvider', doc.uri)) || [];
            if (!symbols.length) await new Promise((r) => setTimeout(r, 100));
        }
        assert.deepStrictEqual(symbols.map((s) => s.name), ['P', 'doble', 'Main']);
        assert.deepStrictEqual(symbols[0].children.map((s) => s.name), ['x']);
        const edit = await vscode.commands.executeCommand('vscode.executeDocumentRenameProvider', doc.uri,
                                                          new vscode.Position(7, 12), 'triple');
        assert(await vscode.workspace.applyEdit(edit));
        assert.match(doc.getText(), /func triple\(n: Int\)/);
        assert.match(doc.getText(), /Print triple\(3\)/);
        fs.rmSync(dir, { recursive: true, force: true });
    });
    await check('language server: format document', async () => {
        const path = require('path');
        const os = require('os');
        const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'dash_it_'));
        const file = path.join(dir, 'formato.dash');
        fs.writeFileSync(file, 'Main\nif 1 > 0\nPrint 1\nend\nend\n');
        const doc = await vscode.workspace.openTextDocument(file);
        await vscode.window.showTextDocument(doc);
        let edits = [];
        for (let i = 0; i < 150 && !(edits && edits.length); i++) {
            edits = await vscode.commands.executeCommand('vscode.executeFormatDocumentProvider', doc.uri,
                                                         { tabSize: 4, insertSpaces: true });
            if (!(edits && edits.length)) await new Promise((r) => setTimeout(r, 100));
        }
        const we = new vscode.WorkspaceEdit();
        we.set(doc.uri, edits);
        assert(await vscode.workspace.applyEdit(we));
        assert.strictEqual(doc.getText(), 'Main\n    if 1 > 0\n        Print 1\n    end\nend\n');
        fs.rmSync(dir, { recursive: true, force: true });
    });
    await check('tasks: the compile task of the provider makes the program', async () => {
        const path = require('path');
        const os = require('os');
        const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'dash_it_'));
        const file = path.join(dir, 'tarea.dash');
        fs.writeFileSync(file, 'Main\n    Print "hola"\nend\n');
        const doc = await vscode.workspace.openTextDocument(file);
        await vscode.window.showTextDocument(doc);
        const tasks = await vscode.tasks.fetchTasks({ type: 'dash' });
        const kinds = tasks.map((t) => t.definition.task).sort();
        assert.deepStrictEqual(kinds, ['compile', 'memcheck', 'profile', 'run'], JSON.stringify(tasks.map((t) => [t.name, t.definition])));
        const compile = tasks.find((t) => t.definition.task === 'compile');
        const done = new Promise((resolve) => {
            const sub = vscode.tasks.onDidEndTaskProcess((e) => {
                if (e.execution.task.name === compile.name) { sub.dispose(); resolve(e.exitCode); }
            });
        });
        await vscode.tasks.executeTask(compile);
        const code = await Promise.race([done, new Promise((r) => setTimeout(() => r('timeout'), 120000))]);
        assert.strictEqual(code, 0);
        assert(fs.existsSync(path.join(dir, 'bin', 'tarea')), 'no bin/tarea');
        const lenses = await vscode.commands.executeCommand('vscode.executeCodeLensProvider', doc.uri);
        assert(lenses.some((l) => l.command && l.command.command === 'dash.runInEmulator'));
        fs.rmSync(dir, { recursive: true, force: true });
    });
    const runKind = async (file, kind) => {
        const doc = await vscode.workspace.openTextDocument(file);
        await vscode.window.showTextDocument(doc);
        const task = (await vscode.tasks.fetchTasks({ type: 'dash' })).find((t) => t.definition.task === kind);
        const done = new Promise((resolve) => {
            const sub = vscode.tasks.onDidEndTask((e) => {
                if (e.execution.task.name === task.name) { sub.dispose(); resolve(true); }
            });
        });
        await vscode.tasks.executeTask(task);
        const ended = await Promise.race([done, new Promise((r) => setTimeout(() => r('timeout'), 240000))]);
        assert.strictEqual(ended, true, 'the task did not end');
        return doc;
    };
    await check('tasks: the run task runs the program in the emulator (hidden) and ends', async () => {
        const path = require('path');
        const os = require('os');
        await vscode.workspace.getConfiguration('dash.emulator').update('window', false, vscode.ConfigurationTarget.Global);
        const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'dash_it_'));
        const file = path.join(dir, 'corre.dash');
        fs.writeFileSync(file, 'Main\n    Print "hola desde el Amiga"\nend\n');
        await runKind(file, 'run');
        assert((await vscode.commands.getCommands(true)).includes('dash.chooseMachine'));
        fs.rmSync(dir, { recursive: true, force: true });
    });
    await check('tasks: a --memcheck error lands on its line', async () => {
        const path = require('path');
        const os = require('os');
        const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'dash_it_'));
        const file = path.join(dir, 'memoria.dash');
        fs.writeFileSync(file, 'struct P\n    x: Int = 0\nend\nMain\n    var p: P = nil\n    Print p.x\nend\n');
        const doc = await runKind(file, 'memcheck');
        let diags = [];
        for (let i = 0; i < 50 && !diags.length; i++) {
            diags = vscode.languages.getDiagnostics(doc.uri).filter((d) => /campo de nil/.test(d.message));
            if (!diags.length) await new Promise((r) => setTimeout(r, 100));
        }
        assert.strictEqual(diags.length, 1, JSON.stringify(vscode.languages.getDiagnostics(doc.uri)));
        assert.strictEqual(diags[0].range.start.line, 5);
        fs.rmSync(dir, { recursive: true, force: true });
    });
    await check('tasks: --profile opens its table', async () => {
        const path = require('path');
        const os = require('os');
        const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'dash_it_'));
        const file = path.join(dir, 'perfil.dash');
        fs.writeFileSync(file, 'func vuelta(n: Int) -> Int\n    t = 0\n    for i in (1..n)\n        t = t + i % 7\n    end\n' +
                               '    return t\nend\nMain\n    s = 0\n    for k in (1..300)\n        s = s + vuelta(2000)\n    end\n' +
                               '    Print s\nend\n');
        await runKind(file, 'profile');
        let tab = null;
        for (let i = 0; i < 50 && !tab; i++) {
            tab = vscode.window.tabGroups.all.flatMap((g) => g.tabs).find((t) => t.label === 'Perfil: perfil.dash');
            if (!tab) await new Promise((r) => setTimeout(r, 100));
        }
        assert(tab, 'no profile panel');
        fs.rmSync(dir, { recursive: true, force: true });
    });
    fs.writeFileSync(process.env.DASH_IT_RESULT, results.join('\n') + '\n');
    await vscode.commands.executeCommand('workbench.action.closeWindow');
}

module.exports = { run };
