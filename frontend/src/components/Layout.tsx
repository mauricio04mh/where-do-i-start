import type { ReactNode } from "react";

type LayoutProps<TabId extends string> = {
  tabs: Array<{ id: TabId; label: string }>;
  activeTab: TabId;
  onTabChange: (tab: TabId) => void;
  children: ReactNode;
};

function Layout<TabId extends string>({
  tabs,
  activeTab,
  onTabChange,
  children,
}: LayoutProps<TabId>) {
  return (
    <div className="app-shell">
      <header className="app-header">
        <div>
          <h1>Where Do I Start</h1>
          <p>Generador de rutas de aprendizaje</p>
        </div>
      </header>

      <nav className="tab-nav" aria-label="Navegacion principal">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            className={tab.id === activeTab ? "active" : ""}
            type="button"
            onClick={() => onTabChange(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </nav>

      <main className="content">{children}</main>
    </div>
  );
}

export default Layout;
