import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { 
  Search, 
  FileText, 
  MessageSquare, 
  CheckCircle, 
  AlertCircle,
  Play,
  Clock,
  TrendingUp,
  Users,
  Zap
} from 'lucide-react';
import FeatureResearchForm from '../components/FeatureResearchForm';
import CommentManager from '../components/CommentManager';
import ResearchStatus from '../components/ResearchStatus';

export default function Home() {
  const [activeTab, setActiveTab] = useState<'research' | 'comments'>('research');
  const [currentSession, setCurrentSession] = useState<string | null>(null);

  const tabs = [
    {
      id: 'research',
      name: 'Feature Research',
      icon: Search,
      description: 'Research features and create PRDs'
    },
    {
      id: 'comments',
      name: 'Comment Management',
      icon: MessageSquare,
      description: 'Manage Linear issue comments'
    }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center space-x-3">
              <div className="flex items-center justify-center w-10 h-10 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-lg">
                <Zap className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Feature Research Agent</h1>
                <p className="text-sm text-gray-600">AI-powered feature research and project management</p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2 text-sm text-gray-600">
                <CheckCircle className="w-4 h-4 text-green-500" />
                <span>Portia Cloud Connected</span>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Tab Navigation */}
        <div className="mb-8">
          <nav className="flex space-x-8" aria-label="Tabs">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as 'research' | 'comments')}
                  className={`
                    group relative min-w-0 flex-1 overflow-hidden py-4 px-6 text-center text-sm font-medium hover:text-gray-700 focus:z-10 focus:outline-none
                    ${activeTab === tab.id
                      ? 'text-blue-600 border-b-2 border-blue-600'
                      : 'text-gray-500 hover:text-gray-700 border-b-2 border-transparent'
                    }
                  `}
                >
                  <div className="flex items-center justify-center space-x-2">
                    <Icon className="w-5 h-5" />
                    <span className="font-medium">{tab.name}</span>
                  </div>
                  <p className="text-xs text-gray-400 mt-1">{tab.description}</p>
                </button>
              );
            })}
          </nav>
        </div>

        {/* Tab Content */}
        <div className="space-y-8">
          {activeTab === 'research' && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3 }}
            >
              <div className="bg-white rounded-xl shadow-lg border border-gray-200 overflow-hidden">
                <div className="px-6 py-4 border-b border-gray-200 bg-gradient-to-r from-blue-50 to-indigo-50">
                  <h2 className="text-lg font-semibold text-gray-900 flex items-center space-x-2">
                    <Search className="w-5 h-5 text-blue-600" />
                    <span>Feature Research & Analysis</span>
                  </h2>
                  <p className="text-sm text-gray-600 mt-1">
                    Research features using AI-powered web search and create comprehensive PRDs
                  </p>
                </div>
                
                <div className="p-6">
                  <FeatureResearchForm 
                    onSessionStart={setCurrentSession}
                    currentSession={currentSession}
                  />
                  
                  {currentSession && (
                    <div className="mt-6">
                      <ResearchStatus sessionId={currentSession} />
                    </div>
                  )}
                </div>
              </div>
            </motion.div>
          )}

          {activeTab === 'comments' && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3 }}
            >
              <div className="bg-white rounded-xl shadow-lg border border-gray-200 overflow-hidden">
                <div className="px-6 py-4 border-b border-gray-200 bg-gradient-to-r from-green-50 to-emerald-50">
                  <h2 className="text-lg font-semibold text-gray-900 flex items-center space-x-2">
                    <MessageSquare className="w-5 h-5 text-green-600" />
                    <span>Linear Comment Management</span>
                  </h2>
                  <p className="text-sm text-gray-600 mt-1">
                    View, create, and manage comments on Linear issues
                  </p>
                </div>
                
                <div className="p-6">
                  <CommentManager />
                </div>
              </div>
            </motion.div>
          )}
        </div>

        {/* Features Overview */}
        <div className="mt-12">
          <div className="text-center mb-8">
            <h2 className="text-2xl font-bold text-gray-900">Powerful Features</h2>
            <p className="text-gray-600 mt-2">Everything you need for feature research and project management</p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[
              {
                icon: Search,
                title: "AI-Powered Research",
                description: "Comprehensive web search and analysis using advanced AI models"
              },
              {
                icon: FileText,
                title: "PRD Generation",
                description: "Automatically create detailed Product Requirements Documents in Notion"
              },
              {
                icon: TrendingUp,
                title: "Linear Integration",
                description: "Create issues and tasks directly in Linear with intelligent task breakdown"
              },
              {
                icon: MessageSquare,
                title: "Comment Management",
                description: "Monitor and manage comments on Linear issues with validation workflows"
              },
              {
                icon: Users,
                title: "Team Collaboration",
                description: "Share research findings and coordinate implementation across teams"
              },
              {
                icon: Zap,
                title: "Real-time Updates",
                description: "Track research progress and get instant notifications on completion"
              }
            ].map((feature, index) => {
              const Icon = feature.icon;
              return (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3, delay: index * 0.1 }}
                  className="bg-white rounded-lg shadow-md border border-gray-200 p-6 hover:shadow-lg transition-shadow"
                >
                  <div className="flex items-center justify-center w-12 h-12 bg-blue-100 rounded-lg mb-4">
                    <Icon className="w-6 h-6 text-blue-600" />
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">{feature.title}</h3>
                  <p className="text-gray-600 text-sm">{feature.description}</p>
                </motion.div>
              );
            })}
          </div>
        </div>
      </main>
    </div>
  );
}
