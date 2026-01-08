import { useState} from "react";
import { useNavigate, Navigate } from "react-router-dom";
import { isAuthed, setToken } from "../utils/auth";
import './LoginPage.css';

const API_URL = "http://127.0.0.1:8000"

export default function LoginPage() {
    const navigate = useNavigate();
    if(isAuthed()) {
        return <Navigate to="/" replace/>
    }
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [status, setStatus] = useState<string>("");

    async function handleLogin() {
        const body = new URLSearchParams();
        body.append("username", username);
        body.append("password", password);
        const response = await fetch(`${API_URL}/token`, {
            method: "POST",
            body: body
        });
        if (!response.ok) {
            setStatus("Login failed");
            return;
        }
        const data = await response.json();
        setToken(data.access_token);
        navigate("/app", { replace: true });
    }
    return (
        <div style={{ border: "1px solid #ccc", padding: 12, marginBottom: 12 }}>
        <h3>Login</h3>

        <input
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            placeholder="username"
            style={{ display: "block", marginBottom: 8 }}
        />
        <input
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="password"
            type="password"
            style={{ display: "block", marginBottom: 8 }}
        />

        <button onClick={handleLogin}>Login</button>
        <div style={{ marginTop: 8 }}>{status}</div>
        </div>
    );
}