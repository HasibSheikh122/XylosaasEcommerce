document.addEventListener("DOMContentLoaded", function() {
    // কনফিগারেশন
    const CONFIG = {
        videoList: [
            "/static/media/bg-video3.mp4",
            "/static/media/bg-video4.mp4",
            "/static/media/bg-video1.mp4",
            "/static/media/bg-video2.mp4",
            "/static/media/bg-video.mp4",
        ],
        intervalDuration: 160000, // ১৬০ সেকেন্ড
        playbackRate: 0.5, // স্লো মোশন
        fadeDuration: 1000, // ফেইড ট্রানজিশন সময় (মিলিসেকেন্ড)
        preload: true, // ভিডিও প্রিলোড করা হবে কি না
    };

    let currentIndex = 0;
    let isTransitioning = false;
    
    // ভিডিও এলিমেন্ট তৈরি
    const video = document.createElement('video');
    video.id = 'bg-video';
    video.autoplay = true;
    video.muted = true;
    video.loop = false;
    video.playsInline = true;
    video.playbackRate = CONFIG.playbackRate;
    video.preload = CONFIG.preload ? 'auto' : 'metadata';
    
    // ভিডিও স্টাইলিং (স্মুথ স্টাইল)
    Object.assign(video.style, {
        position: 'fixed',
        top: '50%',
        left: '50%',
        minWidth: '100%',
        minHeight: '100%',
        width: 'auto',
        height: 'auto',
        transform: 'translate(-50%, -50%) scale(1.1)',
        objectFit: 'cover',
        zIndex: '-1',
        opacity: '1',
        transition: `opacity ${CONFIG.fadeDuration}ms ease-in-out`,
        backgroundColor: '#000',
    });

    // ভিডিও লোডার তৈরি (লোডিং ইন্ডিকেটর)
    const loader = document.createElement('div');
    Object.assign(loader.style, {
        position: 'fixed',
        top: '50%',
        left: '50%',
        transform: 'translate(-50%, -50%)',
        zIndex: '-1',
        color: '#fff',
        fontSize: '16px',
        fontFamily: 'Arial, sans-serif',
        opacity: '0',
        transition: 'opacity 0.5s ease',
    });
    loader.textContent = '📹 লোড হচ্ছে...';
    document.body.prepend(loader);

    // ভিডিও প্লে করার ফাংশন
    function playVideo(index, fadeIn = true) {
        if (isTransitioning) return;
        isTransitioning = true;

        // লোডার দেখানো
        loader.style.opacity = '1';

        const newSrc = CONFIG.videoList[index];
        video.src = newSrc;
        video.playbackRate = CONFIG.playbackRate;

        // ভিডিও লোড হওয়া পর্যন্ত অপেক্ষা
        video.addEventListener('loadeddata', function onLoaded() {
            video.removeEventListener('loadeddata', onLoaded);
            
            // ফেইড ইন
            if (fadeIn) {
                video.style.opacity = '0';
                setTimeout(() => {
                    video.play().catch(() => {});
                    video.style.opacity = '1';
                }, 50);
            } else {
                video.play().catch(() => {});
                video.style.opacity = '1';
            }

            // লোডার লুকানো
            loader.style.opacity = '0';
            
            setTimeout(() => {
                isTransitioning = false;
            }, CONFIG.fadeDuration + 100);
        });

        // ভিডিও লোড না হলে error handling
        video.addEventListener('error', function onError() {
            video.removeEventListener('error', onError);
            loader.textContent = '⚠️ ভিডিও লোড হয়নি, পরবর্তী চেষ্টা...';
            
            setTimeout(() => {
                loader.textContent = '📹 লোড হচ্ছে...';
                // পরবর্তী ভিডিও চেষ্টা
                currentIndex = (currentIndex + 1) % CONFIG.videoList.length;
                playVideo(currentIndex, true);
            }, 2000);
        });
    }

    // ভিডিও যোগ করা
    document.body.prepend(video);
    document.body.prepend(loader);

    // প্রথম ভিডিও প্লে
    playVideo(currentIndex, false);

    // ইন্টারভ্যালে ভিডিও পরিবর্তন
    setInterval(function() {
        if (!isTransitioning) {
            currentIndex = (currentIndex + 1) % CONFIG.videoList.length;
            playVideo(currentIndex, true);
        }
    }, CONFIG.intervalDuration);

    // ভিডিও শেষ হলে পরবর্তী ভিডিওতে চলে যাওয়া (ব্যাকআপ)
    video.addEventListener('ended', function() {
        if (!isTransitioning) {
            currentIndex = (currentIndex + 1) % CONFIG.videoList.length;
            playVideo(currentIndex, true);
        }
    });

    // উইন্ডো রিসাইজ হলে ভিডিও রিপজিশন
    window.addEventListener('resize', function() {
        video.style.transform = 'translate(-50%, -50%) scale(1.1)';
    });

    // কীবোর্ড শর্টকাট (ডিবাগিং এর জন্য)
    document.addEventListener('keydown', function(e) {
        if (e.key === 'ArrowRight' && !isTransitioning) {
            currentIndex = (currentIndex + 1) % CONFIG.videoList.length;
            playVideo(currentIndex, true);
        } else if (e.key === 'ArrowLeft' && !isTransitioning) {
            currentIndex = (currentIndex - 1 + CONFIG.videoList.length) % CONFIG.videoList.length;
            playVideo(currentIndex, true);
        }
    });

    // কনসোলে হেল্পার ফাংশন
    console.log('🎬 ভিডিও প্লেয়ার লোড হয়েছে!');
    console.log(`📹 মোট ভিডিও: ${CONFIG.videoList.length}`);
    console.log('⌨️ শর্টকাট: ← → কী দিয়ে ভিডিও চেঞ্জ করুন');
});

// র্যান্ডম শেপ অ্যাসাইন করা
document.addEventListener('DOMContentLoaded', function() {
    const shapes = [
        'circle-card', 'oval-card', 'hexagon-card', 'star-card',
        'diamond-card', 'pill-card', 'square-rounded', 'floating-card',
        'wave-card', 'glass-card', 'tilt-card'
    ];
    
    document.querySelectorAll('.dashboard-apps .app').forEach(function(app, index) {
        const randomShape = shapes[index % shapes.length];
        app.classList.add(randomShape);
    });
});