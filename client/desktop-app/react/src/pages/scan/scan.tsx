import {useState} from "react";
import {invoke as invokeRust} from "@tauri-apps/api/core";
import {open} from "@tauri-apps/api/dialog";

function ScanPage() {
    const [folderPath, setFolderPath] = useState("");
    const [isScanning, setIsScanning] = useState(false);

    async function handleSelectFolder() {
        const selected = await open({
            directory: true,
            multiple: false,
            defaultPath: folderPath || undefined,
        });
        
        if (selected && typeof selected === 'string') {
            setFolderPath(selected);
        }
    }

    async function handleScan() {
        try {
            setIsScanning(true);
            await invokeRust("scan_folder_and_queue_tasks", {folderPath});
            await invokeRust("perform_tasks");
        } finally {
            setIsScanning(false);
        }
    }

    return (
        <main className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
            <div className="max-w-md mx-auto">
                <div className="text-center">
                    <h1 className="text-2xl font-semibold text-gray-900 mb-8">
                        Folder Scanner
                    </h1>
                    <p className="text-gray-600 mb-8">
                        Select a folder to scan and search through its contents.
                    </p>
                </div>

                <form 
                    onSubmit={(e) => {
                        e.preventDefault();
                        handleScan();
                    }}
                    className="space-y-4"
                >
                    <div className="relative">
                        <input
                            type="text"
                            value={folderPath}
                            onChange={(e) => setFolderPath(e.currentTarget.value)}
                            placeholder="Enter folder path..."
                            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all"
                        />
                    </div>

                    <button
                        type="submit"
                        disabled={isScanning || !folderPath}
                        className="w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {isScanning ? 'Scanning...' : 'Scan Folder'}
                    </button>

                    {folderPath && (
                        <p className="text-sm text-gray-500 mt-4">
                            Selected folder: {folderPath}
                        </p>
                    )}
                </form>
            </div>
        </main>
    );
}

export default ScanPage;
