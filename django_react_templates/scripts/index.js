require('@babel/register')({
  presets: ['@babel/preset-env', '@babel/preset-react']
})

const templatePath = process.argv[2]

if (!templatePath) {
  throw new Error('Missing required argument: path to template')
}

const render = require('./render').default
const html = render(templatePath)

// TODO: Figure out hydration

process.stdout.write(html)
