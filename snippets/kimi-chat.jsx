export const KimiChat = () => {
  const [apiKey, setApiKey] = useState("");
  const [baseUrl, setBaseUrl] = useState("https://api.moonshot.cn/v1");
  const [model, setModel] = useState("kimi-latest");
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [showSettings, setShowSettings] = useState(false);
  const listRef = useRef(null);

  const SYSTEM_PROMPT =
    "你是 NEC-Claw，NEC 新能源开发者社区的云端 AI 助手。" +
    "你熟悉机器人竞赛（ROBOCON、RoboMaster、智能车）、机械设计、嵌入式开发、机器视觉与社区运营，" +
    "请用简洁、专业的中文回答问题，涉及安全操作时务必提醒风险。";

  useEffect(() => {
    try {
      const saved = window.localStorage.getItem("nec_kimi_api_key");
      if (saved) setApiKey(saved);
    } catch (e) {}
  }, []);

  useEffect(() => {
    if (listRef.current) {
      listRef.current.scrollTop = listRef.current.scrollHeight;
    }
  }, [messages, loading]);

  const saveKey = (value) => {
    setApiKey(value);
    try {
      window.localStorage.setItem("nec_kimi_api_key", value);
    } catch (e) {}
  };

  const appendDelta = (delta) => {
    setMessages((prev) => {
      const next = [...prev];
      const last = next[next.length - 1];
      if (last && last.role === "assistant") {
        next[next.length - 1] = { ...last, content: last.content + delta };
      }
      return next;
    });
  };

  const sendMessage = async () => {
    const text = input.trim();
    if (!text || loading) return;
    setError("");

    if (!apiKey.trim()) {
      setError("请先填写 Kimi API Key（点击右上角「设置」）。");
      setShowSettings(true);
      return;
    }

    const history = [...messages, { role: "user", content: text }];
    setMessages([...history, { role: "assistant", content: "" }]);
    setInput("");
    setLoading(true);

    try {
      const apiMessages = [
        { role: "system", content: SYSTEM_PROMPT },
        ...history.map((m) => ({ role: m.role, content: m.content })),
      ];

      const res = await fetch(`${baseUrl.replace(/\/+$/, "")}/chat/completions`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${apiKey.trim()}`,
        },
        body: JSON.stringify({
          model: model.trim() || "kimi-latest",
          messages: apiMessages,
          stream: true,
          temperature: 0.6,
        }),
      });

      if (!res.ok) {
        const text = await res.text();
        throw new Error(`HTTP ${res.status}：${text.slice(0, 300)}`);
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop();
        for (const line of lines) {
          const t = line.trim();
          if (!t.startsWith("data:")) continue;
          const data = t.slice(5).trim();
          if (!data || data === "[DONE]") continue;
          try {
            const json = JSON.parse(data);
            const delta =
              json.choices && json.choices[0] && json.choices[0].delta
                ? json.choices[0].delta.content || ""
                : "";
            if (delta) appendDelta(delta);
          } catch (e) {}
        }
      }
    } catch (e) {
      setError(`请求失败：${e.message || e}`);
      setMessages((prev) => {
        const next = [...prev];
        const last = next[next.length - 1];
        if (last && last.role === "assistant" && !last.content) next.pop();
        return next;
      });
    } finally {
      setLoading(false);
    }
  };

  const clearChat = () => {
    setMessages([]);
    setError("");
  };

  const onKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const colors = {
    border: "#2A2B30",
    panel: "#141519",
    text: "#E5E7EB",
    subtext: "#9CA3AF",
    userBg: "#0066FF",
    assistantBg: "#1C1D22",
    danger: "#F87171",
  };

  const inputStyle = {
    width: "100%",
    background: "#0F1013",
    border: `1px solid ${colors.border}`,
    borderRadius: "6px",
    color: colors.text,
    padding: "6px 10px",
    fontSize: "13px",
    outline: "none",
    boxSizing: "border-box",
  };

  return (
    <div
      style={{
        border: `1px solid ${colors.border}`,
        borderRadius: "12px",
        background: colors.panel,
        overflow: "hidden",
        margin: "16px 0",
      }}
    >
      {/* Header */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "10px 16px",
          borderBottom: `1px solid ${colors.border}`,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <span
            style={{
              width: "8px",
              height: "8px",
              borderRadius: "50%",
              background: apiKey ? "#34D399" : "#6B7280",
              display: "inline-block",
            }}
          />
          <span style={{ color: colors.text, fontWeight: 600, fontSize: "14px" }}>
            NEC-Claw 云端对话
          </span>
          <span style={{ color: colors.subtext, fontSize: "12px" }}>
            由 Kimi API 驱动 · {model}
          </span>
        </div>
        <div style={{ display: "flex", gap: "8px" }}>
          <button
            onClick={() => setShowSettings(!showSettings)}
            style={{
              background: "transparent",
              border: `1px solid ${colors.border}`,
              borderRadius: "6px",
              color: colors.subtext,
              fontSize: "12px",
              padding: "4px 10px",
              cursor: "pointer",
            }}
          >
            设置
          </button>
          <button
            onClick={clearChat}
            style={{
              background: "transparent",
              border: `1px solid ${colors.border}`,
              borderRadius: "6px",
              color: colors.subtext,
              fontSize: "12px",
              padding: "4px 10px",
              cursor: "pointer",
            }}
          >
            清空对话
          </button>
        </div>
      </div>

      {/* Settings */}
      {showSettings && (
        <div
          style={{
            padding: "12px 16px",
            borderBottom: `1px solid ${colors.border}`,
            display: "flex",
            flexDirection: "column",
            gap: "10px",
          }}
        >
          <div>
            <label style={{ color: colors.subtext, fontSize: "12px", display: "block", marginBottom: "4px" }}>
              Kimi API Key（仅保存在本机浏览器 localStorage，不会上传到 NEC 服务器）
            </label>
            <input
              type="password"
              value={apiKey}
              onChange={(e) => saveKey(e.target.value)}
              placeholder="sk-..."
              style={inputStyle}
            />
          </div>
          <div style={{ display: "flex", gap: "10px", flexWrap: "wrap" }}>
            <div style={{ flex: "1 1 200px" }}>
              <label style={{ color: colors.subtext, fontSize: "12px", display: "block", marginBottom: "4px" }}>
                模型
              </label>
              <input
                type="text"
                value={model}
                onChange={(e) => setModel(e.target.value)}
                placeholder="kimi-latest"
                style={inputStyle}
              />
            </div>
            <div style={{ flex: "2 1 260px" }}>
              <label style={{ color: colors.subtext, fontSize: "12px", display: "block", marginBottom: "4px" }}>
                API Base URL（如需走自建代理可修改）
              </label>
              <input
                type="text"
                value={baseUrl}
                onChange={(e) => setBaseUrl(e.target.value)}
                placeholder="https://api.moonshot.cn/v1"
                style={inputStyle}
              />
            </div>
          </div>
        </div>
      )}

      {/* Messages */}
      <div
        ref={listRef}
        style={{
          height: "420px",
          overflowY: "auto",
          padding: "16px",
          display: "flex",
          flexDirection: "column",
          gap: "12px",
        }}
      >
        {messages.length === 0 && (
          <div style={{ color: colors.subtext, fontSize: "13px", textAlign: "center", marginTop: "40px" }}>
            <p style={{ margin: "0 0 8px" }}>👋 你好，我是 NEC-Claw 云端助手。</p>
            <p style={{ margin: 0 }}>
              可以问我机械设计、嵌入式、视觉或竞赛相关问题。首次使用请先在「设置」中填入 Kimi API Key。
            </p>
          </div>
        )}
        {messages.map((m, i) => (
          <div
            key={i}
            style={{
              alignSelf: m.role === "user" ? "flex-end" : "flex-start",
              maxWidth: "85%",
              background: m.role === "user" ? colors.userBg : colors.assistantBg,
              color: colors.text,
              borderRadius: "10px",
              padding: "8px 12px",
              fontSize: "14px",
              lineHeight: 1.6,
              whiteSpace: "pre-wrap",
              wordBreak: "break-word",
            }}
          >
            {m.content || (loading && i === messages.length - 1 ? "思考中…" : "")}
          </div>
        ))}
      </div>

      {/* Error */}
      {error && (
        <div
          style={{
            padding: "8px 16px",
            color: colors.danger,
            fontSize: "13px",
            borderTop: `1px solid ${colors.border}`,
            whiteSpace: "pre-wrap",
            wordBreak: "break-word",
          }}
        >
          {error}
        </div>
      )}

      {/* Input */}
      <div
        style={{
          display: "flex",
          gap: "8px",
          padding: "12px 16px",
          borderTop: `1px solid ${colors.border}`,
          alignItems: "flex-end",
        }}
      >
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={onKeyDown}
          placeholder="输入消息，Enter 发送，Shift+Enter 换行"
          rows={2}
          style={{
            ...inputStyle,
            resize: "vertical",
            minHeight: "40px",
            maxHeight: "120px",
            fontFamily: "inherit",
          }}
        />
        <button
          onClick={sendMessage}
          disabled={loading}
          style={{
            background: loading ? "#1F2937" : colors.userBg,
            border: "none",
            borderRadius: "6px",
            color: "#FFFFFF",
            fontSize: "14px",
            padding: "8px 20px",
            cursor: loading ? "not-allowed" : "pointer",
            flexShrink: 0,
          }}
        >
          {loading ? "发送中…" : "发送"}
        </button>
      </div>
    </div>
  );
};
