import { defineConfig } from 'rollup';
import resolve from '@rollup/plugin-node-resolve';
import commonjs from '@rollup/plugin-commonjs';
import typescript from '@rollup/plugin-typescript';
import { terser } from 'rollup-plugin-terser';

export default defineConfig({
  input: 'src/index.ts',
  output: [
    {
      file: 'dist/node/index.js',
      format: 'cjs',
      exports: 'named',
      sourcemap: true
    },
    {
      file: 'dist/node/index.esm.js',
      format: 'es',
      sourcemap: true
    }
  ],
  external: [
    'fs',
    'fs/promises',
    'path',
    'crypto',
    'better-sqlite3',
    'js-yaml',
    'marked',
    'toml'
  ],
  plugins: [
    resolve({
      preferBuiltins: true
    }),
    commonjs(),
    typescript({
      tsconfig: './tsconfig.json',
      declaration: false,
      declarationMap: false
    }),
    terser({
      compress: {
        drop_console: true
      }
    })
  ]
});