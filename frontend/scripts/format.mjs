#!/usr/bin/env node
import { spawnSync } from 'node:child_process'
import { existsSync } from 'node:fs'
import path from 'node:path'

const args = process.argv.slice(2)
const isCheck = args.includes('--check')
const positional = []
const flags = []

for (const arg of args) {
  if (arg === '--check') continue
  if (arg.startsWith('-')) {
    flags.push(arg)
  } else {
    positional.push(arg)
  }
}

const cwd = process.cwd()
const normalizePath = input => {
  let candidate = input
  if (candidate.startsWith('frontend/')) {
    candidate = candidate.slice('frontend/'.length)
  } else if (candidate.startsWith('./frontend/')) {
    candidate = candidate.slice('./frontend/'.length)
  }

  const resolved = path.resolve(cwd, candidate)
  if (!resolved.startsWith(cwd) || !existsSync(resolved)) {
    return null
  }

  return path.relative(cwd, resolved)
}

const normalizedTargets = Array.from(new Set(positional.map(normalizePath).filter(Boolean)))

const targets = normalizedTargets.length > 0 ? normalizedTargets : ['.']
const prettierArgs = [
  'prettier',
  '--ignore-unknown',
  ...(isCheck ? ['--check'] : ['--write']),
  ...flags,
  ...targets,
]

const result = spawnSync('pnpm', prettierArgs, { stdio: 'inherit', shell: false })

if (result.error) {
  console.error(result.error)
  process.exit(1)
}

process.exit(result.status ?? 1)
