# AgentToast Development To-Do List

## Phase 1: Core Feature Development

### Backend Development
- **News Scraping Agent**
  - [x] Implement API calls for news sources with APIs (e.g., NewsAPI)
  - [ ] Develop web scraping scripts using BeautifulSoup or Scrapy for selected news websites
  - [x] Add error handling: retry failed requests and log inaccessible sources
  - [x] Filter out irrelevant content based on user preferences
  - [ ] Add more news sources and categories
  - [x] Implement rate limiting and request caching

- **Summarization Agent**
  - [x] Integrate OpenAI Agent SDK for text summarization
  - [x] Build a pipeline to process raw article text into concise summaries
  - [x] Ensure summaries are neutral and engaging
  - [ ] Add fallback: use first paragraph of article if summarization fails
  - [x] Log errors for failed summarizations
  - [x] Add retry mechanism for failed API calls
  - [ ] Implement batch processing for multiple articles

- **Audio Generation Agent**
  - [x] Integrate OpenAI TTS for text-to-speech conversion
  - [x] Create a system to generate compiled digests
  - [x] Set default voice selection
  - [x] Ensure audio quality is at least 128 kbps
  - [x] Add error handling and logging
  - [ ] Implement audio chunking for long digests
  - [ ] Add background music options (optional)
  - [ ] Optimize audio file size

### Local Storage System
- **File Management**
  - [x] Set up local storage structure for audio files
  - [x] Implement markdown storage for summaries
  - [x] Create metadata storage system
  - [x] Add file cleanup routine for old digests
  - [ ] Implement file compression
  - [ ] Add backup system for local files

### Workflow Orchestration
- **Scheduler and Task Management**
  - [x] Set up Celery for task scheduling
  - [x] Implement task chaining (scraping → summarization → audio)
  - [x] Add retry mechanisms for failed tasks
  - [x] Implement task monitoring and alerts
  - [x] Add task prioritization
  - [x] Set up task queues for different types of processing

## Phase 2: User Experience and Testing

### User Management
- **User System**
  - [x] Create simple user identification system
  - [x] Implement user preferences storage
  - [x] Add user-specific digest scheduling
  - [x] Create user digest history view

### Testing Suite
- **Unit Tests**
  - [ ] Test NewsScraperAgent
  - [ ] Test SummarizerAgent
  - [ ] Test AudioGeneratorAgent
  - [ ] Test storage functions
  - [ ] Test Celery tasks

- **Integration Tests**
  - [ ] Test end-to-end digest generation
  - [ ] Test error handling and recovery
  - [ ] Test concurrent user processing
  - [ ] Test storage limits and cleanup

### Performance Optimization
- **System Optimization**
  - [x] Implement caching for API responses
  - [x] Optimize memory usage during processing
  - [x] Add request rate limiting
  - [x] Implement batch processing where applicable

### Documentation
- **Code Documentation**
  - [x] Add detailed docstrings to all functions
  - [ ] Create API documentation
  - [ ] Write setup and deployment guides
  - [ ] Document error codes and troubleshooting

## Phase 3: Enhancement and Polish

### Feature Enhancements
- **Content Customization**
  - [ ] Add support for more news categories
  - [ ] Implement content filtering options
  - [ ] Add custom voice selection
  - [ ] Support multiple languages

- **Audio Enhancements**
  - [ ] Add chapter markers in audio files
  - [ ] Implement variable playback speeds
  - [ ] Add sound effects for transitions
  - [ ] Support different audio formats

### System Improvements
- **Monitoring and Logging**
  - [x] Set up comprehensive logging system
  - [x] Add performance monitoring
  - [x] Implement error tracking
  - [x] Create admin dashboard

- **Security**
  - [x] Implement basic authentication
  - [x] Add rate limiting for API endpoints
  - [x] Set up secure file permissions
  - [x] Add input validation and sanitization

## Ongoing Tasks
- **Maintenance**
  - [x] Monitor system performance
  - [x] Update dependencies regularly
  - [x] Clean up old files
  - [x] Optimize storage usage

- **Development**
  - [x] Refactor code based on usage patterns
  - [x] Improve error handling
  - [x] Add new features based on feedback
  - [x] Optimize resource usage

This to-do list reflects our current progress and future goals for the AgentToast project, focusing on a simplified, file-based approach while maintaining robust functionality and user experience.
