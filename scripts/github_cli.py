#!/usr/bin/env python3
"""Run GitHub CLI using its login or the existing Git credential helper."""
import os
import subprocess
import sys


def environment():
    env = dict(os.environ)
    if env.get('GH_TOKEN') or env.get('GITHUB_TOKEN'):
        return env
    native = subprocess.run(['gh', 'auth', 'token', '--hostname', 'github.com'],
                            text=True, capture_output=True)
    if native.returncode == 0 and native.stdout.strip():
        env['GH_TOKEN'] = native.stdout.strip()
        return env
    # Reuse the OS credential store without copying a token into a file or
    # asking for additional OAuth scopes unrelated to release publication.
    result = subprocess.run(['git', '-c', 'credential.interactive=false', 'credential', 'fill'],
                            input='protocol=https\nhost=github.com\n\n', text=True,
                            capture_output=True, env={**env, 'GIT_TERMINAL_PROMPT': '0'})
    fields = dict(line.split('=', 1) for line in result.stdout.splitlines() if '=' in line)
    if result.returncode != 0 or not fields.get('password'):
        raise ValueError('Sign in with gh auth login, or configure your GitHub Git credential helper.')
    env['GH_TOKEN'] = fields['password']
    return env


if __name__ == '__main__':
    try:
        env = environment()
        os.execvpe('gh', ['gh', *sys.argv[1:]], env)
    except (OSError, ValueError) as error:
        raise SystemExit(str(error))
