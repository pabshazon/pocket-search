import { useState } from "react";
import { invoke as invokeRust } from "@tauri-apps/api/core";
import "./style/App.css";

function App() {
  const [folderPath, setFolderPath] = useState("");

  async function callrust() {
    await invokeRust("scan_folder_and_queue_tasks", { folderPath });
    await invokeRust("perform_tasks");
  }

  return (
    <main className="container">
      <h1>Welcome to Pocket-Search</h1>
      <div className="row">
        Logo here
      </div>
      <p>Select a folder to scan and search.</p>

      <form
        className="row"
        onSubmit={(e) => {
          e.preventDefault();
          callrust();
        }}
      >
        <input
          id="greet-input"
          onChange={(e) => setFolderPath(e.currentTarget.value)}
          placeholder="Enter a folder path..."
        />
        <button type="submit">Scan Folder</button>
      </form>
      <p>Folder selected: {folderPath}</p>
    </main>
  );
}

export default App;
