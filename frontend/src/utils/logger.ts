import { isProduction, isDevelopment } from '../config/environment';

type LogLevel = 'debug' | 'info' | 'warn' | 'error';

interface LoggerConfig {
  level: LogLevel;
  enableConsole: boolean;
  prefix?: string;
}

class Logger {
  private static instance: Logger;
  private config: LoggerConfig = {
    level: isProduction ? 'warn' : 'debug',
    enableConsole: !isProduction,
    prefix: '🌿 VeinDiagram'
  };

  private readonly levelPriority: Record<LogLevel, number> = {
    debug: 0,
    info: 1,
    warn: 2,
    error: 3
  };

  private constructor() {}

  static getInstance(): Logger {
    if (!Logger.instance) {
      Logger.instance = new Logger();
    }
    return Logger.instance;
  }

  private shouldLog(level: LogLevel): boolean {
    return this.levelPriority[level] >= this.levelPriority[this.config.level];
  }

  private formatMessage(level: LogLevel, message: string): string {
    const timestamp = new Date().toISOString();
    return `${this.config.prefix} [${level.toUpperCase()}] [${timestamp}]: ${message}`;
  }

  // Sanitize potentially sensitive data
  private sanitizeData(data: any): any {
    if (!data) return data;
    
    // If it's not an object, return as is
    if (typeof data !== 'object') return data;
    
    // Clone the data to avoid modifying the original
    const sanitized = Array.isArray(data) ? [...data] : { ...data };
    
    const sensitiveKeys = [
      'password',
      'token',
      'secret',
      'key',
      'auth',
      'authorization',
      'cookie',
      'session',
      'jwt',
      'apiKey',
      'accessToken',
      'refreshToken',
      'private',
      'credential',
      'ssn',
      'email',
      'phone',
      'address',
      'payment',
      'card',
      'account',
      'username'
    ];

    const sanitizeValue = (key: string, value: any): any => {
      // Check if the key contains any sensitive words
      const isKeySensitive = sensitiveKeys.some(sensitiveKey => 
        key.toLowerCase().includes(sensitiveKey.toLowerCase())
      );

      if (isKeySensitive) {
        return '[REDACTED]';
      }

      // Handle nested objects
      if (value && typeof value === 'object') {
        return this.sanitizeData(value);
      }

      return value;
    };

    // Process each property
    Object.keys(sanitized).forEach(key => {
      sanitized[key] = sanitizeValue(key, sanitized[key]);
    });

    return sanitized;
  }

  debug(message: string, ...args: any[]): void {
    if (this.shouldLog('debug') && this.config.enableConsole && !isProduction) {
      const sanitizedArgs = args.map(arg => this.sanitizeData(arg));
      console.debug(this.formatMessage('debug', message), ...sanitizedArgs);
    }
  }

  info(message: string, ...args: any[]): void {
    if (this.shouldLog('info') && this.config.enableConsole) {
      const sanitizedArgs = args.map(arg => this.sanitizeData(arg));
      console.info(this.formatMessage('info', message), ...sanitizedArgs);
    }
  }

  warn(message: string, ...args: any[]): void {
    if (this.shouldLog('warn') && this.config.enableConsole) {
      const sanitizedArgs = args.map(arg => this.sanitizeData(arg));
      console.warn(this.formatMessage('warn', message), ...sanitizedArgs);
    }
  }

  error(message: string, error?: Error | unknown, ...args: any[]): void {
    if (this.shouldLog('error') && this.config.enableConsole) {
      console.error(this.formatMessage('error', message));
      
      if (error) {
        if (error instanceof Error) {
          const sanitizedError = {
            name: error.name,
            message: error.message,
            // Only include stack trace in development
            stack: isDevelopment ? error.stack : undefined
          };
          console.error('Error details:', sanitizedError);
        } else {
          console.error('Error details:', this.sanitizeData(error));
        }
      }
      
      if (args.length > 0) {
        const sanitizedArgs = args.map(arg => this.sanitizeData(arg));
        console.error('Additional information:', ...sanitizedArgs);
      }
    }
  }

  // API specific logging
  logAPIRequest(method: string, url: string, data?: any): void {
    if (isDevelopment) {
      // Remove query parameters and sensitive parts from URL
      const sanitizedUrl = url.split('?')[0].replace(/\/[0-9a-f-]{36}/g, '/[ID]');
      
      this.debug(`API Request: ${method} ${sanitizedUrl}`, {
        method,
        url: sanitizedUrl,
        // Don't log request data in production
        ...(isDevelopment && data ? { data: this.sanitizeData(data) } : {})
      });
    }
  }

  logAPIResponse(method: string, url: string, status: number): void {
    if (isDevelopment) {
      // Remove query parameters and sensitive parts from URL
      const sanitizedUrl = url.split('?')[0].replace(/\/[0-9a-f-]{36}/g, '/[ID]');
      this.debug(`API Response: ${method} ${sanitizedUrl} - Status: ${status}`);
    }
  }

  logAPIError(method: string, url: string, error: any): void {
    // Remove query parameters and sensitive parts from URL
    const sanitizedUrl = url.split('?')[0].replace(/\/[0-9a-f-]{36}/g, '/[ID]');
    this.error(`API Error: ${method} ${sanitizedUrl}`, this.sanitizeData(error));
  }

  // Auth specific logging
  logAuth(message: string, ...args: any[]): void {
    if (isDevelopment) {
      const sanitizedArgs = args.map(arg => this.sanitizeData(arg));
      this.info(`[Auth] ${message}`, ...sanitizedArgs);
    }
  }

  // Performance logging
  logPerformance(operation: string, duration: number): void {
    if (isDevelopment) {
      this.debug(`Performance - ${operation}: ${duration}ms`);
    }
  }
}

export const logger = Logger.getInstance(); 