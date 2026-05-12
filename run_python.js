const { spawn } = require('child_process');
const py = spawn('./venv/bin/python', ['check_strokes.py']);

py.stdout.on('data', (data) => {
  console.log(`STDOUT: ${data}`);
});

py.stderr.on('data', (data) => {
  console.error(`STDERR: ${data}`);
});

py.on('close', (code) => {
  console.log(`CHILD EXITED WITH CODE ${code}`);
});
