import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react-swc'
import Pages from 'vite-plugin-pages'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
    plugins: [
        react(),
        tailwindcss(),
        Pages({
            dirs: 'src/pages',
            extensions: ['tsx'],
        })
    ],
    preview: {
        port: 4186,
    },
    server: {
        port: 4186,
        host: true,
    },
})
