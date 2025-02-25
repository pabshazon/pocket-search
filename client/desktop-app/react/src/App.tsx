import usePageRouter from "./hooks/usePageRouter.tsx";

import "./styles/App.css";
import ScanPage from "./pages/scan/scan.tsx";
import SearchPage from "./pages/search/search.tsx";

function App() {

  const pageUri = usePageRouter();

  const Page = () => {
    switch(pageUri) {
      case "/":
        return <ScanPage/>;
      case "/scan":
        return <ScanPage/>;
      case "/search":
        return <SearchPage/>;
      default:
        return <div>Error</div>;
    }
  };

  return (
      <>
        <Page/>
      </>
  );
}

export default App;
