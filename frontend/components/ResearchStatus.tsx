import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  Clock, 
  CheckCircle, 
  AlertCircle, 
  Search, 
  FileText, 
  TrendingUp,
  MessageSquare,
  Zap
} from 'lucide-react';
import axios from 'axios';

interface ResearchStatusProps {
  sessionId: string;
}

interface ResearchSession {
  session_id: string;
  status: string;
  progress: number;
  result: any;
  error: string | null;
}

const API_BASE_URL = 'http://localhost:8000';

const statusConfig = {
  initializing: {
    label: 'Initializing',
    icon: Clock,
    color: 'text-blue-600',
    bgColor: 'bg-blue-100',
    description: 'Setting up the research environment...'
  },
  setting_up: {
    label: 'Setting Up',
    icon: Zap,
    color: 'text-blue-600',
    bgColor: 'bg-blue-100',
    description: 'Configuring Portia and tools...'
  },
  researching: {
    label: 'Researching',
    icon: Search,
    color: 'text-yellow-600',
    bgColor: 'bg-yellow-100',
    description: 'Searching web and analyzing information...'
  },
  creating_prd: {
    label: 'Creating PRD',
    icon: FileText,
    color: 'text-purple-600',
    bgColor: 'bg-purple-100',
    description: 'Generating Product Requirements Document...'
  },
  creating_linear_issue: {
    label: 'Creating Linear Issue',
    icon: TrendingUp,
    color: 'text-indigo-600',
    bgColor: 'bg-indigo-100',
    description: 'Setting up project management tasks...'
  },
  completed: {
    label: 'Completed',
    icon: CheckCircle,
    color: 'text-green-600',
    bgColor: 'bg-green-100',
    description: 'Research workflow completed successfully!'
  },
  failed: {
    label: 'Failed',
    icon: AlertCircle,
    color: 'text-red-600',
    bgColor: 'bg-red-100',
    description: 'Research workflow encountered an error'
  }
};

export default function ResearchStatus({ sessionId }: ResearchStatusProps) {
  const [session, setSession] = useState<ResearchSession | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const response = await axios.get(`${API_BASE_URL}/research/${sessionId}`);
        setSession(response.data);
      } catch (error) {
        console.error('Failed to fetch research status:', error);
      } finally {
        setIsLoading(false);
      }
    };

    // Fetch immediately
    fetchStatus();

    // Poll every 2 seconds if not completed or failed
    const interval = setInterval(() => {
      if (session && !['completed', 'failed'].includes(session.status)) {
        fetchStatus();
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [sessionId, session?.status]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-3 text-gray-600">Loading status...</span>
      </div>
    );
  }

  if (!session) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <div className="flex items-center space-x-2">
          <AlertCircle className="w-5 h-5 text-red-600" />
          <span className="text-red-800 font-medium">Error</span>
        </div>
        <p className="text-red-700 mt-1">Failed to load research status</p>
      </div>
    );
  }

  const config = statusConfig[session.status as keyof typeof statusConfig] || statusConfig.initializing;
  const Icon = config.icon;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm"
    >
      {/* Status Header */}
      <div className="flex items-center space-x-3 mb-4">
        <div className={`w-10 h-10 ${config.bgColor} rounded-full flex items-center justify-center`}>
          <Icon className={`w-5 h-5 ${config.color}`} />
        </div>
        <div>
          <h3 className="text-lg font-semibold text-gray-900">{config.label}</h3>
          <p className="text-sm text-gray-600">{config.description}</p>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="mb-6">
        <div className="flex justify-between text-sm text-gray-600 mb-2">
          <span>Progress</span>
          <span>{Math.round(session.progress)}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <motion.div
            className="bg-gradient-to-r from-blue-500 to-indigo-600 h-2 rounded-full"
            initial={{ width: 0 }}
            animate={{ width: `${session.progress}%` }}
            transition={{ duration: 0.5, ease: "easeOut" }}
          />
        </div>
      </div>

      {/* Status Details */}
      <div className="space-y-3">
        <div className="flex justify-between text-sm">
          <span className="text-gray-600">Session ID:</span>
          <span className="font-mono text-gray-900">{session.session_id}</span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-gray-600">Status:</span>
          <span className={`font-medium ${config.color}`}>{config.label}</span>
        </div>
      </div>

      {/* Results Display */}
      {session.result && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          className="mt-6 pt-6 border-t border-gray-200"
        >
          <h4 className="text-md font-semibold text-gray-900 mb-3">Research Results</h4>
          <div className="bg-gray-50 rounded-lg p-4 space-y-3">
            <div className="flex items-center space-x-2">
              <Search className="w-4 h-4 text-blue-600" />
              <span className="text-sm text-gray-700">
                <strong>Feature:</strong> {session.result.feature_name}
              </span>
            </div>
            
            {session.result.notion_page_id && (
              <div className="flex items-center space-x-2">
                <FileText className="w-4 h-4 text-purple-600" />
                <span className="text-sm text-gray-700">
                  <strong>Notion PRD:</strong> Created successfully
                </span>
              </div>
            )}
            
            {session.result.linear_issue_id && (
              <div className="flex items-center space-x-2">
                <TrendingUp className="w-4 h-4 text-indigo-600" />
                <span className="text-sm text-gray-700">
                  <strong>Linear Issue:</strong> {session.result.linear_issue_id}
                </span>
              </div>
            )}
          </div>
        </motion.div>
      )}

      {/* Error Display */}
      {session.error && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-6 pt-6 border-t border-gray-200"
        >
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex items-center space-x-2">
              <AlertCircle className="w-5 h-5 text-red-600" />
              <span className="text-red-800 font-medium">Error Details</span>
            </div>
            <p className="text-red-700 mt-1 text-sm">{session.error}</p>
          </div>
        </motion.div>
      )}

      {/* Action Buttons */}
      {session.status === 'completed' && (
        <div className="mt-6 pt-6 border-t border-gray-200">
          <div className="flex space-x-3">
            <button className="flex-1 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors">
              View Full Analysis
            </button>
            <button className="flex-1 bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg transition-colors">
              Open in Linear
            </button>
          </div>
        </div>
      )}

      {session.status === 'failed' && (
        <div className="mt-6 pt-6 border-t border-gray-200">
          <button className="w-full bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg transition-colors">
            Retry Research
          </button>
        </div>
      )}
    </motion.div>
  );
}
