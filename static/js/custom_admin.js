document.addEventListener("DOMContentLoaded", function() {
    var videoList = [
        "/static/media/bg-video.mp4",
        "/static/media/bg-video1.mp4",
        "/static/media/bg-video2.mp4",
        "/static/media/bg-video3.mp4",
        "/static/media/bg-video4.mp4",
    ];
    
    var currentIndex = 0;
    var video = document.createElement('video');
    
    video.id = 'bg-video';
    video.autoplay = true;
    video.muted = true;
    video.loop = false; // ইন্টারভ্যালের জন্য লুপ ফলস রাখা হয়েছে
    video.playsInline = true;
    
    // ভিডিও স্লো মোশন করার জন্য (0.5 = অর্ধেক গতি)
    video.playbackRate = 0.5; 
    
    // ভিডিওটি বডিতে যোগ করা
    video.src = videoList[currentIndex];
    document.body.prepend(video);
    
    // ১৬০ সেকেন্ড (১৬০,০০০ মিলিসেকেন্ড) পরপর ভিডিও পরিবর্তন করার লজিক
    setInterval(function() {
        currentIndex++;
        
        if (currentIndex >= videoList.length) {
            currentIndex = 0;
        }
        
        video.src = videoList[currentIndex];
        video.playbackRate = 0.5; // নতুন ভিডিওর জন্য পুনরায় রেট সেট করা
        video.play();
    }, 160000); 
});