import usePageRouter  from "./hooks/usePageRouter.tsx";
import ScanPage       from "./pages/scan/scan.tsx";
import SearchPage     from "./pages/search/search.tsx";
import "./styles/App.css";

function App() {

  const currentPageUri = usePageRouter();

  const Page = () => {
    switch(currentPageUri) {
      case "/":
        return <ScanPage/>;
      case "/scan":
        return <ScanPage/>;
      case "/search":
        return <SearchPage/>;
      default:
        return <div className="p-4 text-red-600 dark:text-red-400">Error: Page not found</div>;
    }
  };

  return (
      <>
        <Page/>
      </>
  );
}

export default App;
