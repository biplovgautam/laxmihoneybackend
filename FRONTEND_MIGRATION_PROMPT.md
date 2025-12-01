# GitHub Copilot Prompt: Migrate ChatbotWidget to New Multi-Turn Backend

## Context
Update the existing React ChatbotWidget component to integrate with a new FastAPI backend that supports:
- Multi-turn conversation with chat history
- Firebase authentication for logged-in users
- Anonymous sessions for non-authenticated users
- Secure token-based authentication
- Chat history retrieval and clearing
- Redis-based session memory

## Current Backend Endpoints

### 1. Public Chat (Non-authenticated)
```
POST /api1/llm/public
Headers: Content-Type: application/json
Body: {
  "message": "user message",
  "anonymousId": "anon-uuid-12345"
}
Response: {
  "message": "user message",
  "response": "bot response",
  "user_type": "public",
  "anonymous_id": "anon-uuid-12345",
  "model": "llama-3.1-8b-instant",
  "status": "success"
}
```

### 2. Authenticated Chat (Logged-in users)
```
POST /api1/llm/authenticated
Headers: 
  Content-Type: application/json
  Authorization: Bearer <firebase-id-token>
Body: {
  "message": "user message"
}
Response: {
  "message": "user message",
  "response": "bot response",
  "user_type": "authenticated",
  "user_id": "firebase-uid",
  "model": "llama-3.1-8b-instant",
  "status": "success"
}
```

### 3. Get Chat History
```
GET /api1/llm/history?anonymousId=anon-uuid (for anonymous)
GET /api1/llm/history (with Authorization header for authenticated)
Headers: 
  Authorization: Bearer <firebase-id-token> (optional, for authenticated users)
Response: {
  "history": [
    {"role": "user", "content": "message"},
    {"role": "assistant", "content": "response"}
  ],
  "user_type": "authenticated" | "anonymous",
  "message_count": 10,
  "status": "success"
}
```

### 4. Clear Chat History (Authenticated only)
```
DELETE /api1/llm/clearchat
Headers: 
  Authorization: Bearer <firebase-id-token>
Response: {
  "status": "success",
  "message": "Chat history cleared successfully",
  "user_id": "firebase-uid"
}
```

## Requirements

### 1. Anonymous User Session Management
- Generate a unique `anonymousId` using UUID v4 when the chatbot first loads
- Store `anonymousId` in localStorage with key `chatbot_anonymous_id`
- Retrieve existing `anonymousId` from localStorage on component mount
- Send `anonymousId` with every request to `/api1/llm/public`
- Anonymous sessions expire after 24 hours on the backend

### 2. Firebase Authentication Integration
- Check for Firebase auth token in localStorage (key: `authToken`)
- Use authenticated endpoint (`/api1/llm/authenticated`) when user is logged in
- Include `Authorization: Bearer <token>` header for authenticated requests
- Fallback to public endpoint if no valid token exists
- Handle 401 Unauthorized errors by falling back to public endpoint

### 3. Chat History Loading
- On chatbot open, fetch chat history from backend using GET `/api1/llm/history`
- For authenticated users: send Authorization header
- For anonymous users: send `anonymousId` as query parameter
- Populate messages state with historical messages
- Display loading indicator while fetching history
- Handle empty history gracefully (show welcome message)

### 4. Enhanced UI Features
Add these new buttons to the chat header:
- **"View History" button**: Fetches and displays full conversation history
- **"Clear Chat" button**: 
  - Only visible for authenticated users
  - Shows confirmation dialog before clearing
  - Calls DELETE `/api1/llm/clearchat`
  - Clears local messages state and re-initializes with welcome message
  - Shows success toast notification

### 5. Error Handling & Security
- Handle network errors gracefully with user-friendly messages
- Implement retry logic for failed requests (max 2 retries)
- Validate responses from backend before processing
- Never expose Firebase tokens in error messages or logs
- Show specific error messages for:
  - 400 Bad Request (missing anonymousId)
  - 401 Unauthorized (invalid token)
  - 500 Internal Server Error (backend issues)
  - Network timeout errors

### 6. Session Persistence
- Persist anonymousId across page refreshes
- Load chat history on component mount (not just when opening chat)
- Show "Restoring conversation..." indicator when loading history
- Sync messages state with backend history on initialization

### 7. Improved UX
- Show "(Logged in)" or "(Guest)" indicator in chat header
- Add message count indicator (e.g., "12 messages in this conversation")
- Implement auto-scroll to bottom when new messages arrive
- Add "New conversation" button (clears local state, generates new anonymousId for anonymous users)
- Show timestamp for each message
- Implement message character limit (e.g., 500 chars) with counter

## Code Structure Guidelines

### Helper Functions to Create
```typescript
// Generate or retrieve anonymous ID
const getOrCreateAnonymousId = () => {
  let anonId = localStorage.getItem('chatbot_anonymous_id');
  if (!anonId) {
    anonId = `anon-${crypto.randomUUID()}`;
    localStorage.setItem('chatbot_anonymous_id', anonId);
  }
  return anonId;
};

// Check authentication status
const getAuthToken = () => {
  return localStorage.getItem('authToken');
};

// Load chat history on mount
const loadChatHistory = async () => {
  // Implement fetch logic with proper headers
};

// Clear chat with confirmation
const handleClearChat = async () => {
  // Implement with confirmation dialog
};
```

### State Variables to Add
```typescript
const [anonymousId, setAnonymousId] = useState('');
const [isLoadingHistory, setIsLoadingHistory] = useState(false);
const [messageCount, setMessageCount] = useState(0);
const [authStatus, setAuthStatus] = useState<'authenticated' | 'anonymous'>('anonymous');
```

### API Request Structure
```typescript
// For authenticated users
const headers = {
  'Content-Type': 'application/json',
  'Authorization': `Bearer ${authToken}`
};

// For anonymous users
const headers = {
  'Content-Type': 'application/json'
};
const body = {
  message: userMessage,
  anonymousId: anonymousId
};
```

## Security Best Practices
1. Never log Firebase tokens to console
2. Validate all user inputs before sending to backend
3. Sanitize bot responses before rendering (prevent XSS)
4. Use HTTPS for all API calls (check API_BASE_URL includes https://)
5. Implement CSRF protection if using cookies
6. Add rate limiting on frontend (max 10 messages per minute)
7. Clear sensitive data from memory when chat is closed

## Migration Steps
1. Add UUID generation utility (or use `crypto.randomUUID()`)
2. Implement `getOrCreateAnonymousId()` function
3. Update `getBotResponseFromLLM()` to include anonymousId for public endpoint
4. Add `loadChatHistory()` function and call it on component mount when chat opens
5. Add "Clear Chat" button with confirmation dialog (authenticated users only)
6. Add authentication status indicator to header
7. Update error handling to cover all new scenarios
8. Add loading states for history fetching
9. Test both authenticated and anonymous flows thoroughly
10. Remove any old code that manually constructed system prompts (backend now handles this)

## Testing Checklist
- [ ] Anonymous user can send messages with auto-generated anonymousId
- [ ] anonymousId persists across page refreshes
- [ ] Chat history loads automatically when opening chatbot
- [ ] Authenticated users see "Clear Chat" button
- [ ] Clear chat works correctly with confirmation
- [ ] Authentication token is sent properly for logged-in users
- [ ] Fallback to public endpoint works if auth fails
- [ ] Error messages are user-friendly
- [ ] UI shows correct authentication status
- [ ] Multi-turn conversation works (backend remembers context)
- [ ] Quick replies still function correctly
- [ ] Mobile responsive design maintained
- [ ] No console errors or warnings

## Important Notes
- Backend now handles all system prompts and conversation context
- Do NOT construct or send system prompts from frontend
- Backend automatically maintains conversation history via Redis
- Each user message receives context from previous conversation turns
- Anonymous sessions expire after 24 hours (backend handles this)
- Authenticated sessions expire after 30 days (backend handles this)

---

## Example: Updated getBotResponseFromLLM Function

```typescript
const getBotResponseFromLLM = async (userMessage: string) => {
  try {
    if (!API_BASE_URL) {
      throw new Error('Backend API base URL is not configured');
    }

    const authToken = getAuthToken();
    const isAuthenticated = !!authToken;
    
    // Determine endpoint based on authentication
    const endpoint = isAuthenticated 
      ? '/api1/llm/authenticated' 
      : '/api1/llm/public';
    
    // Prepare request body
    const requestBody: any = {
      message: userMessage
    };
    
    // Add anonymousId for public endpoint
    if (!isAuthenticated) {
      requestBody.anonymousId = anonymousId;
    }
    
    // Prepare headers
    const headers: any = {
      'Content-Type': 'application/json'
    };
    
    // Add Authorization header for authenticated users
    if (isAuthenticated) {
      headers['Authorization'] = `Bearer ${authToken}`;
    }

    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'POST',
      headers: headers,
      body: JSON.stringify(requestBody),
    });

    if (!response.ok) {
      if (response.status === 401 && isAuthenticated) {
        // Token expired, fallback to public endpoint
        return await getBotResponseFromLLM(userMessage); // Retry as anonymous
      }
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const data = await response.json();
    
    // Update auth status
    setAuthStatus(data.user_type === 'authenticated' ? 'authenticated' : 'anonymous');
    
    return data.response || "I apologize, but I received an unexpected response. Please try again! 🙏";
    
  } catch (error) {
    console.error('Chatbot error:', error);
    return "I apologize, but I'm having trouble processing your request right now. Please try again or contact us directly at +977 981-9492581. 🙏";
  }
};
```

---

**Prompt to use in GitHub Copilot Chat:**

"Update the ChatbotWidget component following the specifications in FRONTEND_MIGRATION_PROMPT.md. Implement anonymous session management with UUID, Firebase authentication support, chat history loading, clear chat functionality, and enhanced error handling. Maintain the existing UI design and animations while adding new features for authenticated users. Ensure security best practices are followed."
