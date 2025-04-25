# TODO List

## Video Download Enhancements

### UI Preview for Downloaded Videos
- [ ] Make downloaded videos appear in UI preview like uploads
  - [ ] Investigate how uploads are displayed in the UI
  - [ ] Add downloaded videos to the same preview system
  - [ ] Ensure preview updates when new videos are downloaded
  - [ ] Handle preview cleanup when videos are removed

### Testing Infrastructure
- [ ] Create test suite for video download functionality
  - [ ] Test direct URL downloads
    - [ ] Test wget download path
    - [ ] Test curl download path
    - [ ] Test fallback to yt-dlp
  - [ ] Test video platform downloads
    - [ ] Test YouTube downloads
    - [ ] Test Vimeo downloads
  - [ ] Test error handling
    - [ ] Invalid URLs
    - [ ] Network failures
    - [ ] Permission issues
  - [ ] Test preview system
    - [ ] Verify preview generation
    - [ ] Test preview updates
    - [ ] Test cleanup

## Implementation Details

### UI Preview System
1. Current upload preview system:
   - Location: Need to identify where upload previews are handled
   - Integration points: Find where to hook in downloaded videos

2. Testing approach:
   - Create pytest test suite
   - Add mock server for testing downloads
   - Add sample videos for testing
   - Set up CI integration
