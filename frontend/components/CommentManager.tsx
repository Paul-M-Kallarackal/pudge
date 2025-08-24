import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  MessageSquare, 
  Plus, 
  Search, 
  Send, 
  User, 
  Calendar,
  AlertCircle,
  CheckCircle,
  Clock
} from 'lucide-react';
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

interface Comment {
  id: string;
  body: string;
  author: {
    id: string;
    name: string;
  };
  createdAt: string;
  updatedAt: string;
}

export default function CommentManager() {
  const [issueId, setIssueId] = useState('');
  const [comments, setComments] = useState<Comment[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newComment, setNewComment] = useState({
    title: '',
    content: ''
  });
  const [isCreating, setIsCreating] = useState(false);

  const fetchComments = async () => {
    if (!issueId.trim()) {
      setError('Please enter an issue ID');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const response = await axios.get(`${API_BASE_URL}/comments/${issueId}`);
      setComments(response.data.comments || []);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch comments. Please try again.');
      setComments([]);
    } finally {
      setIsLoading(false);
    }
  };

  const createComment = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!newComment.content.trim()) {
      setError('Comment content cannot be empty');
      return;
    }

    setIsCreating(true);
    setError(null);

    try {
      const response = await axios.post(`${API_BASE_URL}/comments`, {
        issue_id: issueId,
        title: newComment.title,
        content: newComment.content
      });
      
      if (response.data.success) {
        // Refresh comments
        await fetchComments();
        setNewComment({ title: '', content: '' });
        setShowCreateForm(false);
      } else {
        setError(response.data.message || 'Failed to create comment');
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create comment. Please try again.');
    } finally {
      setIsCreating(false);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="space-y-6">
      {/* Issue ID Input */}
      <div className="flex space-x-4">
        <div className="flex-1">
          <label htmlFor="issueId" className="block text-sm font-medium text-gray-700 mb-2">
            Linear Issue ID
          </label>
          <input
            type="text"
            id="issueId"
            value={issueId}
            onChange={(e) => setIssueId(e.target.value)}
            placeholder="e.g., PRA-9, bcb20267-e98b-4f3b-82aa-5ec0171b18b0"
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-colors"
          />
        </div>
        <div className="flex items-end">
          <button
            onClick={fetchComments}
            disabled={isLoading}
            className={`
              px-6 py-3 rounded-lg font-medium transition-all duration-200 flex items-center space-x-2
              ${isLoading
                ? 'bg-gray-400 cursor-not-allowed'
                : 'bg-green-600 hover:bg-green-700 text-white shadow-lg hover:shadow-xl transform hover:-translate-y-0.5'
              }
            `}
          >
            {isLoading ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                <span>Loading...</span>
              </>
            ) : (
              <>
                <Search className="w-4 h-4" />
                <span>Fetch Comments</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Error Display */}
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

      {/* Comments Display */}
      {comments.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-gray-900">
              Comments ({comments.length})
            </h3>
            <button
              onClick={() => setShowCreateForm(!showCreateForm)}
              className="flex items-center space-x-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
            >
              <Plus className="w-4 h-4" />
              <span>Add Comment</span>
            </button>
          </div>

          {/* Create Comment Form */}
          <AnimatePresence>
            {showCreateForm && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="bg-gray-50 border border-gray-200 rounded-lg p-4"
              >
                <form onSubmit={createComment} className="space-y-4">
                  <div>
                    <label htmlFor="commentTitle" className="block text-sm font-medium text-gray-700 mb-1">
                      Comment Title (optional)
                    </label>
                    <input
                      type="text"
                      id="commentTitle"
                      value={newComment.title}
                      onChange={(e) => setNewComment(prev => ({ ...prev, title: e.target.value }))}
                      placeholder="Brief title for the comment"
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                  <div>
                    <label htmlFor="commentContent" className="block text-sm font-medium text-gray-700 mb-1">
                      Comment Content *
                    </label>
                    <textarea
                      id="commentContent"
                      value={newComment.content}
                      onChange={(e) => setNewComment(prev => ({ ...prev, content: e.target.value }))}
                      rows={3}
                      placeholder="Write your comment here..."
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"
                      required
                    />
                  </div>
                  <div className="flex space-x-3">
                    <button
                      type="submit"
                      disabled={isCreating}
                      className={`
                        flex items-center space-x-2 px-4 py-2 rounded-md font-medium transition-colors
                        ${isCreating
                          ? 'bg-gray-400 cursor-not-allowed'
                          : 'bg-blue-600 hover:bg-blue-700 text-white'
                        }
                      `}
                    >
                      {isCreating ? (
                        <>
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                          <span>Creating...</span>
                        </>
                      ) : (
                        <>
                          <Send className="w-4 h-4" />
                          <span>Post Comment</span>
                        </>
                      )}
                    </button>
                    <button
                      type="button"
                      onClick={() => setShowCreateForm(false)}
                      className="px-4 py-2 text-gray-600 hover:text-gray-800 transition-colors"
                    >
                      Cancel
                    </button>
                  </div>
                </form>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Comments List */}
          <div className="space-y-4">
            {comments.map((comment, index) => (
              <motion.div
                key={comment.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm hover:shadow-md transition-shadow"
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center space-x-3">
                    <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                      <User className="w-4 h-4 text-blue-600" />
                    </div>
                    <div>
                      <p className="font-medium text-gray-900">{comment.author.name}</p>
                      <div className="flex items-center space-x-2 text-sm text-gray-500">
                        <Calendar className="w-3 h-3" />
                        <span>{formatDate(comment.createdAt)}</span>
                        {comment.updatedAt !== comment.createdAt && (
                          <>
                            <span>•</span>
                            <span>Updated {formatDate(comment.updatedAt)}</span>
                          </>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
                <div className="text-gray-700 whitespace-pre-wrap">{comment.body}</div>
              </motion.div>
            ))}
          </div>
        </div>
      )}

      {/* Empty State */}
      {!isLoading && comments.length === 0 && issueId && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-center py-12"
        >
          <MessageSquare className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No comments found</h3>
          <p className="text-gray-600 mb-4">
            This issue doesn't have any comments yet, or the issue ID might be incorrect.
          </p>
          <button
            onClick={() => setShowCreateForm(true)}
            className="inline-flex items-center space-x-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
          >
            <Plus className="w-4 h-4" />
            <span>Add First Comment</span>
          </button>
        </motion.div>
      )}

      {/* Initial State */}
      {!issueId && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-center py-12"
        >
          <Search className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">Enter an Issue ID</h3>
          <p className="text-gray-600">
            Enter a Linear issue ID above to view and manage comments.
          </p>
        </motion.div>
      )}
    </div>
  );
}
