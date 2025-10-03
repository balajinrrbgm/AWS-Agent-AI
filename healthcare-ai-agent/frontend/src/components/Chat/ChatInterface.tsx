import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Paper,
  TextField,
  IconButton,
  Typography,
  Avatar,
  Chip,
  CircularProgress,
  Alert,
  Fab,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  List,
  ListItem,
  ListItemText,
  Card,
  CardContent,
  Grid,
} from '@mui/material';
import {
  Send as SendIcon,
  SmartToy as BotIcon,
  Person as PersonIcon,
  Warning as WarningIcon,
  ReportProblem as EmergencyIcon,
  LocalHospital as HospitalIcon,
  Psychology as PsychologyIcon,
} from '@mui/icons-material';
import { format } from 'date-fns';

// Hooks
import { useAuth } from '../../contexts/AuthContext';
import { useNotification } from '../../contexts/NotificationContext';
import { useHealthAPI } from '../../hooks/useHealthAPI';

// Types
interface Message {
  id: string;
  content: string;
  sender: 'user' | 'assistant';
  timestamp: Date;
  confidence?: number;
  recommendations?: string[];
  riskLevel?: 'low' | 'medium' | 'high' | 'critical';
  requiresHumanReview?: boolean;
}

interface QuickAction {
  id: string;
  label: string;
  icon: React.ReactElement;
  prompt: string;
  color: 'primary' | 'secondary' | 'warning' | 'error';
}

const ChatInterface: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId] = useState(() => `session_${Date.now()}`);
  const [showEmergencyDialog, setShowEmergencyDialog] = useState(false);
  const [emergencyDetails, setEmergencyDetails] = useState<any>(null);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { user } = useAuth();
  const { showNotification } = useNotification();
  const { sendChatMessage } = useHealthAPI();

  // Quick action prompts
  const quickActions: QuickAction[] = [
    {
      id: 'symptoms',
      label: 'Symptom Check',
      icon: <HospitalIcon />,
      prompt: 'I have some symptoms I\'d like to discuss',
      color: 'primary',
    },
    {
      id: 'medication',
      label: 'Medication Help',
      icon: <PsychologyIcon />,
      prompt: 'I have questions about my medications',
      color: 'secondary',
    },
    {
      id: 'emergency',
      label: 'Emergency',
      icon: <EmergencyIcon />,
      prompt: 'This is urgent - I need immediate help',
      color: 'error',
    },
    {
      id: 'wellness',
      label: 'Wellness Check',
      icon: <PersonIcon />,
      prompt: 'I want to discuss my general health and wellness',
      color: 'primary',
    },
  ];

  // Welcome message
  useEffect(() => {
    const welcomeMessage: Message = {
      id: 'welcome',
      content: `Hello ${user?.name || 'there'}! I'm your Healthcare AI Assistant. I'm here to help you with medical questions, symptom analysis, and health guidance. 

How can I assist you today?

**Important**: This AI assistant provides general health information and is not a substitute for professional medical advice. For emergencies, please call 911 or go to your nearest emergency room.`,
      sender: 'assistant',
      timestamp: new Date(),
      confidence: 1.0,
    };
    setMessages([welcomeMessage]);
  }, [user]);

  // Scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSendMessage = async (messageContent?: string) => {
    const content = messageContent || inputValue.trim();
    if (!content) return;

    const userMessage: Message = {
      id: `user_${Date.now()}`,
      content,
      sender: 'user',
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    try {
      const response = await sendChatMessage({
        session_id: sessionId,
        content,
        timestamp: new Date(),
        message_type: 'user',
      });

      const assistantMessage: Message = {
        id: `assistant_${Date.now()}`,
        content: response.response,
        sender: 'assistant',
        timestamp: new Date(),
        confidence: response.confidence,
        recommendations: response.recommendations,
        riskLevel: response.risk_assessment,
        requiresHumanReview: response.requires_human_review,
      };

      setMessages(prev => [...prev, assistantMessage]);

      // Handle emergency situations
      if (response.risk_assessment === 'critical' || response.risk_assessment === 'high') {
        setEmergencyDetails(response);
        setShowEmergencyDialog(true);
        showNotification(
          'High risk situation detected. Please review emergency recommendations.',
          'warning'
        );
      }

      // Show follow-up questions
      if (response.follow_up_questions && response.follow_up_questions.length > 0) {
        setTimeout(() => {
          const followUpMessage: Message = {
            id: `followup_${Date.now()}`,
            content: `To better assist you, I have a few follow-up questions:\n\n${response.follow_up_questions!.map((q: string, i: number) => `${i + 1}. ${q}`).join('\n')}`,
            sender: 'assistant',
            timestamp: new Date(),
            confidence: 0.9,
          };
          setMessages(prev => [...prev, followUpMessage]);
        }, 1000);
      }

    } catch (error) {
      console.error('Chat error:', error);
      showNotification('Failed to send message. Please try again.', 'error');
      
      const errorMessage: Message = {
        id: `error_${Date.now()}`,
        content: 'I apologize, but I\'m experiencing technical difficulties. Please try again or contact support if the issue persists.',
        sender: 'assistant',
        timestamp: new Date(),
        confidence: 0.1,
      };
      
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSendMessage();
    }
  };

  const getRiskColor = (riskLevel?: string) => {
    switch (riskLevel) {
      case 'critical':
        return 'error';
      case 'high':
        return 'warning';
      case 'medium':
        return 'info';
      default:
        return 'success';
    }
  };

  const MessageBubble: React.FC<{ message: Message }> = ({ message }) => (
    <Box
      sx={{
        display: 'flex',
        justifyContent: message.sender === 'user' ? 'flex-end' : 'flex-start',
        mb: 2,
      }}
    >
      <Box
        sx={{
          display: 'flex',
          alignItems: 'flex-start',
          maxWidth: '80%',
          flexDirection: message.sender === 'user' ? 'row-reverse' : 'row',
        }}
      >
        <Avatar
          sx={{
            width: 32,
            height: 32,
            bgcolor: message.sender === 'user' ? 'primary.main' : 'secondary.main',
            mx: 1,
          }}
        >
          {message.sender === 'user' ? <PersonIcon /> : <BotIcon />}
        </Avatar>
        
        <Paper
          elevation={1}
          sx={{
            p: 2,
            bgcolor: message.sender === 'user' ? 'primary.light' : 'grey.100',
            color: message.sender === 'user' ? 'white' : 'text.primary',
            borderRadius: 2,
          }}
        >
          <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
            {message.content}
          </Typography>
          
          {/* Risk Level Indicator */}
          {message.riskLevel && message.sender === 'assistant' && (
            <Box sx={{ mt: 1 }}>
              <Chip
                size="small"
                label={`Risk: ${message.riskLevel.toUpperCase()}`}
                color={getRiskColor(message.riskLevel) as any}
                icon={message.riskLevel === 'critical' ? <WarningIcon /> : undefined}
              />
            </Box>
          )}
          
          {/* Recommendations */}
          {message.recommendations && message.recommendations.length > 0 && (
            <Box sx={{ mt: 2 }}>
              <Typography variant="subtitle2" gutterBottom>
                Recommendations:
              </Typography>
              <List dense>
                {message.recommendations.map((rec, index) => (
                  <ListItem key={index} sx={{ py: 0.5 }}>
                    <ListItemText primary={`• ${rec}`} />
                  </ListItem>
                ))}
              </List>
            </Box>
          )}
          
          {/* Human Review Warning */}
          {message.requiresHumanReview && (
            <Alert severity="warning" sx={{ mt: 1 }}>
              This response requires human review. Please consult with a healthcare professional.
            </Alert>
          )}
          
          <Typography variant="caption" display="block" sx={{ mt: 1, opacity: 0.7 }}>
            {format(message.timestamp, 'HH:mm')}
            {message.confidence && ` • Confidence: ${Math.round(message.confidence * 100)}%`}
          </Typography>
        </Paper>
      </Box>
    </Box>
  );

  return (
    <>
      <Paper elevation={2} sx={{ height: 'calc(100vh - 120px)', display: 'flex', flexDirection: 'column' }}>
        {/* Header */}
        <Box sx={{ p: 2, borderBottom: '1px solid', borderColor: 'divider' }}>
          <Typography variant="h6" color="primary">
            Healthcare AI Assistant
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Your personal medical consultation partner
          </Typography>
        </Box>

        {/* Quick Actions */}
        <Box sx={{ p: 2, borderBottom: '1px solid', borderColor: 'divider' }}>
          <Grid container spacing={1}>
            {quickActions.map((action) => (
              <Grid item key={action.id}>
                <Chip
                  icon={action.icon}
                  label={action.label}
                  clickable
                  color={action.color}
                  variant="outlined"
                  onClick={() => handleSendMessage(action.prompt)}
                  sx={{ mr: 1 }}
                />
              </Grid>
            ))}
          </Grid>
        </Box>

        {/* Messages Area */}
        <Box
          sx={{
            flexGrow: 1,
            overflow: 'auto',
            p: 2,
            bgcolor: 'grey.50',
          }}
        >
          {messages.map((message) => (
            <MessageBubble key={message.id} message={message} />
          ))}
          
          {isLoading && (
            <Box sx={{ display: 'flex', justifyContent: 'flex-start', mb: 2 }}>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <Avatar sx={{ width: 32, height: 32, bgcolor: 'secondary.main', mx: 1 }}>
                  <BotIcon />
                </Avatar>
                <Paper elevation={1} sx={{ p: 2, bgcolor: 'grey.100', borderRadius: 2 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <CircularProgress size={16} />
                    <Typography variant="body2">Analyzing your message...</Typography>
                  </Box>
                </Paper>
              </Box>
            </Box>
          )}
          
          <div ref={messagesEndRef} />
        </Box>

        {/* Input Area */}
        <Box sx={{ p: 2, borderTop: '1px solid', borderColor: 'divider' }}>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <TextField
              fullWidth
              multiline
              maxRows={4}
              placeholder="Describe your symptoms or ask a health question..."
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              disabled={isLoading}
              variant="outlined"
              size="small"
            />
            <IconButton
              color="primary"
              onClick={() => handleSendMessage()}
              disabled={isLoading || !inputValue.trim()}
              sx={{ alignSelf: 'flex-end' }}
            >
              <SendIcon />
            </IconButton>
          </Box>
          
          <Typography variant="caption" color="text.secondary" sx={{ mt: 1 }}>
            Press Enter to send, Shift+Enter for new line
          </Typography>
        </Box>
      </Paper>

      {/* Emergency Dialog */}
      <Dialog
        open={showEmergencyDialog}
        onClose={() => setShowEmergencyDialog(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle sx={{ color: 'error.main' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <EmergencyIcon />
            Emergency Situation Detected
          </Box>
        </DialogTitle>
        
        <DialogContent>
          <Alert severity="error" sx={{ mb: 2 }}>
            Based on your symptoms, this may require immediate medical attention.
          </Alert>
          
          {emergencyDetails && (
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Immediate Actions:
                </Typography>
                <List>
                  {emergencyDetails.recommendations?.map((rec: string, index: number) => (
                    <ListItem key={index}>
                      <ListItemText primary={`• ${rec}`} />
                    </ListItem>
                  ))}
                </List>
                
                <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                  If this is a life-threatening emergency, call 911 immediately.
                </Typography>
              </CardContent>
            </Card>
          )}
        </DialogContent>
        
        <DialogActions>
          <Button onClick={() => setShowEmergencyDialog(false)}>
            I Understand
          </Button>
          <Button variant="contained" color="error" href="tel:911">
            Call 911
          </Button>
        </DialogActions>
      </Dialog>

      {/* Emergency FAB */}
      <Fab
        color="error"
        sx={{
          position: 'fixed',
          bottom: 16,
          right: 16,
        }}
        onClick={() => handleSendMessage('This is urgent - I need immediate help')}
      >
        <EmergencyIcon />
      </Fab>
    </>
  );
};

export default ChatInterface;