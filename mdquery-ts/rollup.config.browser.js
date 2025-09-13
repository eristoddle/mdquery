import { defineConfig } from 'rollup';
import resolve from '@rollup/plugin-node-resolve';
import commonjs from '@rollup/plugin-commonjs';
import typescript from '@rollup/plugin-typescript';
import { terser } from 'rollup-plugin-terser';

export default defineConfig({
  input: 'src/index.ts',
  output: [
    {
      file: 'dist/browser/index.js',
      format: 'umd',
      name: 'MDQuery',
      exports: 'named',
      sourcemap: true,
      globals: {
        'wa-sqlite/dist/wa-sqlite.mjs': 'WASQLite',
        'wa-sqlite/dist/wa-sqlite-async.mjs': 'WASQLiteAsync'
      }
    },
    {
      file: 'dist/browser/index.esm.js',
      format: 'es',
      sourcemap: true
    }
  ],
  external: [
    'wa-sqlite/dist/wa-sqlite.mjs',
    'wa-sqlite/dist/wa-sqlite-async.mjs'
  ],
  plugins: [
    resolve({
      browser: true,
      preferBuiltins: false
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