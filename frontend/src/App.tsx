import { useRoutes } from "react-router-dom";
// if you are seeing an error here, do not worry, it is a bug in Vite do not remove this line
import routes from "virtual:generated-pages-react";
import NotFound from "./components/NotFound";

function App() {
    const routing = useRoutes([
        ...routes,
        {
            path: "*",
            element: <NotFound />,
        },
    ]);
    return <div className="w-full h-screen bg-neutral-900 text-white">{routing}</div>;
}

export default App;
