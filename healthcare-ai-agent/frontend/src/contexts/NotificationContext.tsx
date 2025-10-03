import React, { createContext, useContext, useState, ReactNode } from 'react';
import { Snackbar, Alert, AlertColor } from '@mui/material';

// Types
interface NotificationContextType {
  showNotification: (message: string, severity?: AlertColor, duration?: number) => void;
  hideNotification: () => void;
}

interface NotificationState {
  open: boolean;
  message: string;
  severity: AlertColor;
  duration: number;
}

// Create context
const NotificationContext = createContext<NotificationContextType | undefined>(undefined);

// Notification Provider component
interface NotificationProviderProps {
  children: ReactNode;
}

export const NotificationProvider: React.FC<NotificationProviderProps> = ({ children }) => {
  const [notification, setNotification] = useState<NotificationState>({
    open: false,
    message: '',
    severity: 'info',
    duration: 6000,
  });

  const showNotification = (
    message: string,
    severity: AlertColor = 'info',
    duration: number = 6000
  ): void => {
    setNotification({
      open: true,
      message,
      severity,
      duration,
    });
  };

  const hideNotification = (): void => {
    setNotification(prev => ({
      ...prev,
      open: false,
    }));
  };

  const handleClose = (event?: React.SyntheticEvent | Event, reason?: string): void => {
    if (reason === 'clickaway') {
      return;
    }
    hideNotification();
  };

  const value: NotificationContextType = {
    showNotification,
    hideNotification,
  };

  return (
    <NotificationContext.Provider value={value}>
      {children}
      <Snackbar
        open={notification.open}
        autoHideDuration={notification.duration}
        onClose={handleClose}
        anchorOrigin={{ vertical: 'top', horizontal: 'right' }}
      >
        <Alert 
          onClose={handleClose} 
          severity={notification.severity}
          variant="filled"
          sx={{ width: '100%' }}
        >
          {notification.message}
        </Alert>
      </Snackbar>
    </NotificationContext.Provider>
  );
};

// Hook to use notification context
export const useNotification = (): NotificationContextType => {
  const context = useContext(NotificationContext);
  if (context === undefined) {
    throw new Error('useNotification must be used within a NotificationProvider');
  }
  return context;
};

export default NotificationContext;