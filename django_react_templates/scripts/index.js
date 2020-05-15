const templatePath = process.argv[2]

if (!templatePath) {
  throw new Error('Missing required argument: Path to template')
}

const context = process.argv[3] ? JSON.parse(process.argv[3]) : {}

require('@babel/register')({
  presets: ['@babel/preset-env', '@babel/preset-react']
})

// Load render function from an external module so that we can use babel-register
// to transpile React components
const render = require('./render').default
render(templatePath, context)
