import React, { useState } from 'react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { 
  Box, 
  Container, 
  Typography, 
  Button, 
  Card, 
  CardContent, 
  TextField,
  Alert,
  CircularProgress,
  Tab,
  Tabs
} from '@mui/material';

// Contexts
import { AuthProvider } from './contexts/AuthContext';
import { NotificationProvider } from './contexts/NotificationContext';

// Components
import ChatInterface from './components/Chat/ChatInterface';

// Theme
const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
      light: '#42a5f5',
      dark: '#1565c0',
    },
    secondary: {
      main: '#dc004e',
      light: '#ff5983',
      dark: '#9a0036',
    },
    background: {
      default: '#f5f5f5',
      paper: '#ffffff',
    },
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          borderRadius: 8,
        },
      },
    },
  },
});

// Simple Healthcare Chat Component
const HealthcareChat: React.FC = () => {
  const [query, setQuery] = useState('');
  const [response, setResponse] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError('');

    try {
      const res = await fetch('/consultation/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query }),
      });

      if (res.ok) {
        const data = await res.json();
        setResponse(data.response);
      } else {
        setError('Failed to get response from AI agent');
      }
    } catch (err) {
      setError('Network error. Please check if the backend is running.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card sx={{ maxWidth: 800, mx: 'auto', mt: 4 }}>
      <CardContent>
        <Typography variant="h5" gutterBottom>
          Healthcare AI Agent Chat
        </Typography>
        
        <form onSubmit={handleSubmit}>
          <TextField
            fullWidth
            multiline
            rows={3}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask me about your health concerns..."
            variant="outlined"
            margin="normal"
          />
          
          <Button
            type="submit"
            variant="contained"
            disabled={loading || !query.trim()}
            sx={{ mt: 2 }}
          >
            {loading ? <CircularProgress size={20} /> : 'Ask AI Agent'}
          </Button>
        </form>

        {error && (
          <Alert severity="error" sx={{ mt: 2 }}>
            {error}
          </Alert>
        )}

        {response && (
          <Card sx={{ mt: 3, bgcolor: 'primary.light', color: 'white' }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                AI Response:
              </Typography>
              <Typography variant="body1">
                {response}
              </Typography>
            </CardContent>
          </Card>
        )}
      </CardContent>
    </Card>
  );
};

const App: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  return (
    <AuthProvider>
      <NotificationProvider>
        <ThemeProvider theme={theme}>
          <CssBaseline />
          <Container maxWidth="lg">
            <Box sx={{ py: 4 }}>
              <Typography variant="h2" component="h1" gutterBottom align="center">
                🏥 Healthcare AI Agent
              </Typography>
              
              <Typography variant="h5" component="h2" gutterBottom align="center" color="text.secondary">
                Intelligent Healthcare Assistant powered by AWS AI services
              </Typography>

              <Alert severity="info" sx={{ mt: 3, mb: 3 }}>
                <Typography variant="body2">
                  <strong>Demo Mode:</strong> This is running with mock AWS services for development. 
                  Real implementation uses Amazon Bedrock (Claude 3 Sonnet), SageMaker AI, and 17 other AWS services.
                </Typography>
              </Alert>

              <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 2 }}>
                <Tabs value={tabValue} onChange={handleTabChange} aria-label="healthcare tabs">
                  <Tab label="AI Chat Interface" />
                  <Tab label="Simple Chat" />
                </Tabs>
              </Box>

              {tabValue === 0 && <ChatInterface />}
              {tabValue === 1 && <HealthcareChat />}

              <Box sx={{ mt: 4, p: 3, bgcolor: 'background.paper', borderRadius: 2 }}>
                <Typography variant="h6" gutterBottom>
                  AWS Services Integration:
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  • Amazon Bedrock (Claude 3 Sonnet) • SageMaker AI • DynamoDB • S3 • Cognito 
                  • API Gateway • Lambda • EventBridge • Step Functions • CloudWatch • Textract 
                  • Comprehend Medical • CloudFront • IAM • KMS • VPC • Systems Manager
                </Typography>
              </Box>
            </Box>
          </Container>
        </ThemeProvider>
      </NotificationProvider>
    </AuthProvider>
  );
};

export default App;