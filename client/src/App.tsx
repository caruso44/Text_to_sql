import { useState } from 'react'
import './App.css'


type Session = {
  session_id: string;
  session_name: string;
}

const API_URL = "http://127.0.0.1:8000"


function Question({selectedSessionId}: {selectedSessionId: string | null}) {
  const [text, setText] = useState("");
  const [answer, setAnswer] = useState<string>("");
  
  async function handleClick() {
    const response = await fetch(
      `${API_URL}/run_query_rewoo/${encodeURIComponent(text)}?session_id=${selectedSessionId}`,
      {
        method: "GET"
      }
    );

    const data = await response.json();
    setAnswer(data.message);
}

  return (
    <div> 
      <input
        type="text"
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Ask a question"
      />
      <button onClick={handleClick}>Ask Ai agent</button>
      <p>{answer}</p>
    </div>
  )
}

function SelectSession({selectedSessionId, setSelectedSessionId}: {selectedSessionId: string | null, setSelectedSessionId: (id: string) => void}) {
  const [sessions, setSessions] = useState<Session[]>([]);

  async function fetchSessions() {
    const response = await fetch(`${API_URL}/list_sessions`, {
       method: "GET" 
    });
    const data = await response.json();
    console.log("Data:", data);
    setSessions(data.sessions);
  }

  function handleSessionSelect(sessionId: string) {
      setSelectedSessionId(sessionId);
    }

  return (
    <div>
      <button onClick={() => {
         console.log("CLICKED Load Sessions");
         fetchSessions()}
         }>Load Sessions</button>

      <table style={{ borderCollapse: "collapse", marginTop: "1rem" }}>
        <thead>
          <tr>
            <th style={{ border: "1px solid #ccc", padding: "8px" }}>
              Session ID
            </th>
            <th style={{ border: "1px solid #ccc", padding: "8px" }}>
              Session Name
            </th>
          </tr>
        </thead>

         <tbody>
          {sessions.map((session) => {
            const isSelected = session.session_id === selectedSessionId;

            return (
              <tr
                key={session.session_id}
                onClick={() => handleSessionSelect(session.session_id)}
                style={{
                  cursor: "pointer",
                  backgroundColor: isSelected ? "#e6f2ff" : "transparent",
                }}
              >
                <td style={{ border: "1px solid #ccc", padding: "8px" }}>{session.session_id}</td>
                <td style={{ border: "1px solid #ccc", padding: "8px" }}>{session.session_name}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );

}

function App() {
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null);

  return (
    <div className="App">
      <Question selectedSessionId={selectedSessionId} />
      <SelectSession
        selectedSessionId={selectedSessionId}
        setSelectedSessionId={setSelectedSessionId}
      />
    </div>
  );
}

export default App
