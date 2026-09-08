### Left off -> CH18 Deployment

# - Ch10 Email (Practice SMTP & Web API email setup with providers)
# Notes:
## Workflow:
    * Any backend feature (x), is a machine that transforms intent into a permanent result
    * Every Feature contains 3 layers of complexity
        1. Ingestion (The Wire): Capturing raw data & validating intent.
            * EX. Getting data from the outside world into the server safely. This entails decoding incoming data format (JSON/HTML), checking for malicious inputs, and ensuring data is structurally valid (e.g. "Is this a valid email address?")

        2. Engine (The Logic): Computing, Calculating, and Modifying state.
            * The core calculations to my unique business rules. This entails mathematical operations, permission evaluation, and coordinating state changes (e.g. "Is this user allowed to buy this item?")

        3. Logistics (The Effects): Saving to DB, notifying systems, calling APIs
            * Ensuring the result is permanent. This entails database storage, updating metrics, clearing caches, and triggering external notifications

- How Django handles this workflow WELL
    * Ingestion = django.forms (& DRF Serializers)
        > It automatically cleans, sanitizes, and validates incoming data. Strips out malicious scripts.
    
    * Engine = django.views
        > Standard CRUD business logic. It acts as the traffic controller, routing valid data to the database layer.

    * Logistics = Django ORM (models.py)
        > Converts python code into highly optimized SQL. Manages standard database connections and prevents SQL injection security attacks automatically.

- What django struggles with (This is when to optimize/customize)
    * Django is Synchronous and Thread-Blocked, so when a user triggers a request one of django's worker threads is locked to that user until the entire process finishes. If a step takes 5 seconds then the worker is frozen for those 5 seconds preventing other users from using the app.

## When to step outside of Django's standard architecture and their optimizations:
    * High Latency Operations (Time-Based Complexity)
        > This happens when the feature requires talking to external servers or doing heavy math (e.g. generating PDF's, interacting with a credit card processor API like stripe, or resizing large images)

        > OPTIMIZATION: Keep ingestion in django and move the engine/logistics to an Asynchronous Task Queue (Celery + Redis).

    * Mass Read/Write Volume (Scale-Based Complexity)
        > This happens when a feature involves high-frequency data (e.g. tracking user clicks on a page, real-time IoT sensor logging, or thousands of users requesting a leaderboard simultaneously). Django ORM writes directly to disk storage (SQL). So this High-Frequency writing will choke your database connection pool and crash your site.

        > OPTIMIZATION: Bypass the standard ORM. Routing ingestion through django but storing the fast-moving data in an in-memory database like Redis or a specialized NoSQL database (MongoDB/InfluxDB) and syncing it to your main SQL database only in scheduled/quiet intervals.

    * Bi-Directional Connections (Protocal-Based Complexity)
        > This happens when a feature requires the server to instantly push data to the user without the user refreshing (e.g. real-time chat app or live notification feed). Django is built strictly for http (Request -> Response -> Close Connection) and cannot natively hold open continuous avenues of communication like WebSockets

        > OPTIMIZATION: Use Django Channels and an ASGI server (Daphne) instead of the standard WSGI setup. This expands Django's architecture to support persistent, open WebSocket connections


## Questions I should ask to determine the tools I will use in the workflow:
    1. How long does the feature take to execute?
        > If under 200ms: Use standard Django views/models
        > If over 500ms: plan for asynchronous worker (Celery)

    2. How often will the feature hit the database?
        > If standard user activity: Django ORM to handle it
        > If it's thousands of hits a minute, place a cache layer (Redis) in front of Django.

    3. Does the server need to talk first?
        > If client initiates contact: Standard Django
        > If server needs to push real-time alerts: Use Django Channels

    4. How much will this feature's data structure change over the next year? (Data Volatility)
        > If the data structure is highly predictabl (like an invoice or user profile): Django's standard SQL
        > If the data is unpredictable or deeply nested (like a dynamic quiz where questions change formats): Use a JSONField or an External NoSQL database

    5. What happens if a process in this feature fails halfway through? (Atomicity & Idempotency)
        > If a feature charges a customer and THEN updates their premium account status, What happens if the database crashes right after the payment goes through? - If this is a risk I must wrap the processes in Django's built-in (transaction.atomic()) block so the entire feature rolls back safely if any single part fails

    6. Who is allowed to trigger this feature, and under what exact conditions? (Authorization Strategy)
        > Instead of checking user permissions inside the core logic of the feature, I can decide where to block unauthorized traffic. Does it happen at the URL level (via a decoder @login_required), or through a custom middleware?

- What makes a good question when figuring out the tools I will use in the workflow?
    > Questions asked based on the Primary Constraints of the application

## The 4 Primary Constraint Patterns
    1. "Rich Domain" (Constraint: Data Integrity & Complexity)
        > Typical Apps: E-commerce, Banking, HR platforms, Healthcare Systems
        > The Stack Template: Heavy Relational database (PostgreSQL) + strict Django ORM schemas + automated database transactions
        > Constaint Conceptualized: "Data accuracy is life or death. Speed is important, but a single corrupted database row is an absolute disaster."

    2. "High Concurrency" (Constraint: Mass Scale & Low Latency)
        > Typical Apps: Chat Apps, Live Tracking, Gaming Leaderboards, Ad Tech
        > The Stack Template: Django Channels (WebSockets) + Redis (for in-memory sorting/caching) + NoSQL database wrappers
        > Constraint Conceptualized: "The database cannot keep up with this many writes. We must pull data out of disk storage and hold it in memory, or use event-driven queues."

    3. "Integration Heavy" (Constraint: Third-Party Dependencies)
        > Typical Apps: Travel booking aggregators, AI wrapper tools, complex logistics/shipping platforms
        > The Stack Template: Django + Celery/Redis Workers + robust error logging (Sentry)
        > Constraint Conceptualized: "Our app is only as fast or reliable as the external APIs we call. Everything that talks to an outside server must happen in an isolated background thread with automatic retries."

    4. "Time-To-Market" (Constraint: Speed of Development)
        > Typical Apps: MVPs (Minimum Viable Products), Early-stage startups, proof of concepts
        > The Stack Template: Vanilla Django + SQLite (for local) or simple managed Postgres + Standard Django Admin. Minimal External packages
        > Constraint Conceptualized: "Build it with Django's default batteries today. Optimze for Scale of Integration only when the users show up."

## Testing
    - Write many unit tests (tests that check specific functionality)  and a small number of integration tests (large, slow, and used to test an entire application or user flow like payment that covers multiple screens)
    - To write unit tests [TestCase] is needed


## Production Aspects
    - django-stores (storing all media files on a service like Amazon's S3 Buckets)> A true production website would have a CDN (Content Delivery Network) for storing all media files rather than a server (which we currently have). Always treat user-generated media files with caution. 

    - Hosting services (like Heroku) have an Ephemeral File System which boots a clean copy from the most recent deploy (stored on the docker, kubernetes, AWS Lambda, or Amazon S3). Once the service is shutdown or contianer/pods deleted, the files are also deleted

    - Must contain comprehensive tests

    - Performance becomes the main focus when there's a large amount of traffic to the website. Don't start off at optimization but have metrics to find where optimization is needed. Opimization comes down to 4 areas (database queries, caching, indexes, and compressing front-end images, Javascript, and CSS)