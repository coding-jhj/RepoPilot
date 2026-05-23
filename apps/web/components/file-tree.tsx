export function FileTree() {
  const files = ["README.md", "app/main.py", "app/services/repo_service.py", "tests/test_agent.py"];
  return (
    <section className="panel compact">
      <h2>Evidence Files</h2>
      {files.map((file) => (
        <code key={file}>{file}</code>
      ))}
    </section>
  );
}
