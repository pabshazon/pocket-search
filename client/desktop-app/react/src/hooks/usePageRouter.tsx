import {useEffect, useState} from "react";


function usePageRouter() {
    const [pageUri, setPageUri] = useState(window.location.pathname);

    useEffect(() => {
        const handleBrowsingHistoryPopState = () => {
            setPageUri(window.location.pathname);
        }

        const handleClick  = (clickEvent: MouseEvent) => {
            const eventTarget = clickEvent.target as HTMLAnchorElement;

            if (eventTarget.origin === window.location.origin && eventTarget.tagName === 'A') {
                clickEvent.preventDefault();
                const pageUri = window.location.pathname;
                window.history.pushState(null, "", pageUri);
                setPageUri(pageUri);
            }
        }

        window.addEventListener("popstate", handleBrowsingHistoryPopState);
        document.addEventListener("click", handleClick);

        return function cleanup() {
            window.removeEventListener("popstate", handleBrowsingHistoryPopState);
            document.removeEventListener("click", handleClick);
        };
    }, []);

    return pageUri
}

export default usePageRouter;