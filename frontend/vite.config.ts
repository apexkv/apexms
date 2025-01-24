import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react-swc'

// https://vite.dev/config/
export default defineConfig({
    plugins: [react()],
    preview: {
        port: 4186,
    },
    server: {
        port: 4186,
    },
})
