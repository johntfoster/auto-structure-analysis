# Phase 6: Camera & Mobile UX - Implementation Plan

## Tasks

### 1. Camera Integration with Capacitor ✓
- [ ] Create camera service with Capacitor Camera API
- [ ] Add web fallback for browser testing
- [ ] Update Capture.tsx to use new camera service
- [ ] Add tests for camera service

### 2. ArUco Marker Template Page ✓
- [ ] Create /marker route
- [ ] Build printable marker component
- [ ] Add print styles
- [ ] Link from Capture page
- [ ] Tests for marker page

### 3. Photo Gallery & Thumbnails ✓
- [ ] Update backend API to return thumbnails
- [ ] Enhance History page with thumbnail grid
- [ ] Add image caching
- [ ] Tests for gallery

### 4. Mobile-First Responsive UI ✓
- [ ] Review all pages for mobile responsiveness
- [ ] Add hamburger menu for mobile nav
- [ ] Optimize touch targets (min 44px)
- [ ] Test on various screen sizes

### 5. PWA Support ✓
- [ ] Create manifest.json
- [ ] Add service worker with Workbox
- [ ] Add install prompt component
- [ ] Offline fallback page
- [ ] Update index.html with PWA meta tags

### 6. Dark/Light Theme Toggle ✓
- [ ] Create ThemeContext
- [ ] Add theme toggle button
- [ ] Update all components with theme classes
- [ ] Persist theme preference
- [ ] Tests for theme switching
