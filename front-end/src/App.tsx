import type { Component } from "solid-js";
import { Route, Router } from "@solidjs/router";
import { MainLayout } from "./components/MainLayout";
import { ChatPage } from "./pages/ChatPage";
import { AgentsPage } from "./pages/AgentsPage";
import { AgentFormPage } from "./pages/AgentFormPage";
import { KnowledgeBasesPage } from "./pages/KnowledgeBasesPage";
import { KnowledgeBaseDetailsPage } from "./pages/KnowledgeBaseDetailsPage";
import { ToolsetsPage } from "./pages/ToolsetsPage";
import { ToolsetFormPage } from "./pages/ToolsetFormPage";

const App: Component = () => {
  return (
    <Router root={MainLayout}>
      <Route path="/" component={ChatPage} />
      <Route path="/chat/:id" component={ChatPage} />
      <Route path="/agents" component={AgentsPage} />
      <Route path="/agents/form" component={AgentFormPage} />
      <Route path="/agents/form/:id" component={AgentFormPage} />
      <Route path="/knowledge-bases" component={KnowledgeBasesPage} />
      <Route path="/knowledge-bases/:id" component={KnowledgeBaseDetailsPage} />
      <Route path="/toolsets" component={ToolsetsPage} />
      <Route path="/toolsets/form" component={ToolsetFormPage} />
      <Route path="/toolsets/form/:id" component={ToolsetFormPage} />
    </Router>
  );
};

export default App;
