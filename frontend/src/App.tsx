import { useState } from "react";
import Layout from "./components/Layout";
import ChatPathGenerator from "./components/ChatPathGenerator";
import PathGenerator from "./components/PathGenerator";
import ResourceManager from "./components/ResourceManager";
import StudentManager from "./components/StudentManager";

type Tab = "students" | "resources" | "paths" | "chat";

const tabs: Array<{ id: Tab; label: string }> = [
  { id: "students", label: "Estudiantes" },
  { id: "resources", label: "Recursos" },
  { id: "paths", label: "Generar ruta" },
  { id: "chat", label: "Preguntar" },
];

function App() {
  const [activeTab, setActiveTab] = useState<Tab>("students");

  return (
    <Layout tabs={tabs} activeTab={activeTab} onTabChange={setActiveTab}>
      {activeTab === "students" && <StudentManager />}
      {activeTab === "resources" && <ResourceManager />}
      {activeTab === "paths" && <PathGenerator />}
      {activeTab === "chat" && <ChatPathGenerator />}
    </Layout>
  );
}

export default App;
