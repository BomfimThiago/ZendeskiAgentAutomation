# TeleCorp Chat Frontend

React-based frontend interface for the TeleCorp AI Assistant chat application.

## Features

- 💬 Real-time chat interface with AI assistant
- 🔄 Session management for conversation continuity
- 📱 Responsive design for mobile and desktop
- ⚡ TypeScript for type safety
- 🎨 Modern UI with gradient header and smooth animations
- ✅ Connection status indicator
- ⌨️ Keyboard shortcuts (Enter to send, Shift+Enter for new line)

## Prerequisites

- Node.js 14+ and npm
- Backend server running on `http://localhost:8000`

## Installation

```bash
# Install dependencies
npm install
```

## Configuration

Create a `.env` file in the frontend directory:

```bash
REACT_APP_API_URL=http://localhost:8000/api/v1
```

## Running the Application

```bash
# Start development server
npm start
```

The app will open at [http://localhost:3000](http://localhost:3000)

## Building for Production

```bash
# Create production build
npm run build
```

The build folder will contain the optimized production build.

## Project Structure

```
frontend/
├── src/
│   ├── components/          # React components
│   │   ├── ChatMessage.tsx  # Individual message component
│   │   ├── ChatMessage.css
│   │   ├── ChatInput.tsx    # Message input component
│   │   └── ChatInput.css
│   ├── services/            # API services
│   │   └── api.ts          # Backend API communication
│   ├── App.tsx             # Main application component
│   ├── App.css             # Main styles
│   └── index.tsx           # Application entry point
├── public/                 # Static assets
├── .env                    # Environment variables
└── package.json           # Dependencies and scripts
```

## API Integration

The frontend communicates with the backend through these endpoints:

- `POST /api/v1/ai/chat` - Send chat messages
- `GET /api/v1/ai/chat/hello` - Get welcome message
- `GET /health` - Backend health check

## Available Scripts

- `npm start` - Run development server
- `npm build` - Create production build
- `npm test` - Run tests
- `npm eject` - Eject from Create React App (irreversible)

## Technologies Used

- React 18
- TypeScript
- CSS3 with custom animations
- Fetch API for HTTP requests
