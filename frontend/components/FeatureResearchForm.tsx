import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Search, Play, AlertCircle, CheckCircle } from 'lucide-react';
import axios from 'axios';

interface FeatureResearchFormProps {
  onSessionStart: (sessionId: string) => void;
  currentSession: string | null;
}

const API_BASE_URL = 'http://localhost:8000';

export default function FeatureResearchForm({ onSessionStart, currentSession }: FeatureResearchFormProps) {
  const [formData, setFormData] = useState({
    name: '',
    description: ''
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.name.trim() || !formData.description.trim()) {
      setError('Please fill in all fields');
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      const response = await axios.post(`${API_BASE_URL}/research`, formData);
      
      if (response.data.session_id) {
        onSessionStart(response.data.session_id);
        setFormData({ name: '', description: '' });
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to start research. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    if (error) setError(null);
  };

  if (currentSession) {
    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="bg-green-50 border border-green-200 rounded-lg p-6"
      >
        <div className="flex items-center space-x-3 mb-4">
          <CheckCircle className="w-6 h-6 text-green-600" />
          <h3 className="text-lg font-semibold text-green-800">Research Started!</h3>
        </div>
        <p className="text-green-700 mb-4">
          Your feature research is now running in the background. You can track the progress below.
        </p>
        <button
          onClick={() => onSessionStart('')}
          className="text-green-600 hover:text-green-700 text-sm font-medium underline"
        >
          Start another research
        </button>
      </motion.div>
    );
  }

  return (
    <motion.form
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      onSubmit={handleSubmit}
      className="space-y-6"
    >
      <div>
        <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-2">
          Feature Name *
        </label>
        <input
          type="text"
          id="name"
          name="name"
          value={formData.name}
          onChange={handleInputChange}
          placeholder="e.g., User Authentication, Payment Gateway, Real-time Chat"
          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
          required
        />
      </div>

      <div>
        <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-2">
          Feature Description *
        </label>
        <textarea
          id="description"
          name="description"
          value={formData.description}
          onChange={handleInputChange}
          rows={4}
          placeholder="Describe the feature in detail. What problem does it solve? What are the key requirements? What should it include?"
          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors resize-none"
          required
        />
      </div>

      {error && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-red-50 border border-red-200 rounded-lg p-4"
        >
          <div className="flex items-center space-x-2">
            <AlertCircle className="w-5 h-5 text-red-600" />
            <span className="text-red-800 font-medium">Error</span>
          </div>
          <p className="text-red-700 mt-1">{error}</p>
        </motion.div>
      )}

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-start space-x-3">
          <Search className="w-5 h-5 text-blue-600 mt-0.5" />
          <div>
            <h4 className="text-sm font-medium text-blue-800">What happens next?</h4>
            <ul className="text-sm text-blue-700 mt-2 space-y-1">
              <li>• AI-powered web search for feature information and market analysis</li>
              <li>• Comprehensive feature analysis with technical considerations</li>
              <li>• Automatic PRD creation in Notion (if configured)</li>
              <li>• Linear issue and task creation with intelligent breakdown</li>
            </ul>
          </div>
        </div>
      </div>

      <button
        type="submit"
        disabled={isSubmitting}
        className={`
          w-full flex items-center justify-center space-x-2 px-6 py-3 rounded-lg font-medium transition-all duration-200
          ${isSubmitting
            ? 'bg-gray-400 cursor-not-allowed'
            : 'bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white shadow-lg hover:shadow-xl transform hover:-translate-y-0.5'
          }
        `}
      >
        {isSubmitting ? (
          <>
            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
            <span>Starting Research...</span>
          </>
        ) : (
          <>
            <Play className="w-5 h-5" />
            <span>Start Feature Research</span>
          </>
        )}
      </button>
    </motion.form>
  );
}
