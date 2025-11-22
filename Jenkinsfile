// =============================================================================
// MULTI-AGENT SUPPORT SYSTEM - JENKINS PIPELINE
// Enterprise-grade CI/CD with Jenkins + Kubernetes
// =============================================================================

// Pipeline configuration
def APP_NAME = 'multi-agent-support-system'
def DOCKER_REGISTRY = 'ghcr.io/othmanmohammad'
def K8S_NAMESPACE = 'production'

pipeline {
    agent any

    // Environment variables
    environment {
        // Docker
        DOCKER_BUILDKIT = '1'
        DOCKER_REGISTRY_CREDS = credentials('docker-hub-creds')

        // Git
        GIT_COMMIT_SHORT = sh(script: "git rev-parse --short HEAD", returnStdout: true).trim()
        GIT_BRANCH = sh(script: "git rev-parse --abbrev-ref HEAD", returnStdout: true).trim()

        // Versioning
        VERSION = "${GIT_BRANCH}-${GIT_COMMIT_SHORT}-${BUILD_NUMBER}"

        // Kubernetes
        KUBECONFIG = credentials('kubeconfig')

        // Notifications
        SLACK_CHANNEL = '#deployments'
    }

    // Build triggers
    triggers {
        // Poll GitHub every 5 minutes (or use webhooks)
        pollSCM('H/5 * * * *')

        // Trigger from GitHub webhook
        githubPush()
    }

    // Pipeline options
    options {
        // Keep last 30 builds
        buildDiscarder(logRotator(numToKeepStr: '30'))

        // Timeout after 1 hour
        timeout(time: 1, unit: 'HOURS')

        // Add timestamps to console output
        timestamps()

        // Colored output
        ansiColor('xterm')

        // Disable concurrent builds
        disableConcurrentBuilds()
    }

    // Pipeline parameters (for manual triggers)
    parameters {
        choice(
            name: 'ENVIRONMENT',
            choices: ['staging', 'production'],
            description: 'Deployment environment'
        )
        booleanParam(
            name: 'SKIP_TESTS',
            defaultValue: false,
            description: 'Skip tests (emergency deployments only)'
        )
        booleanParam(
            name: 'FORCE_DEPLOY',
            defaultValue: false,
            description: 'Force deployment even if tests fail'
        )
    }

    stages {
        // =====================================================================
        // STAGE 1: PREPARATION
        // =====================================================================
        stage('🔍 Preparation') {
            steps {
                script {
                    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
                    echo "🚀 BUILD: ${APP_NAME}"
                    echo "📦 VERSION: ${VERSION}"
                    echo "🌿 BRANCH: ${GIT_BRANCH}"
                    echo "📝 COMMIT: ${GIT_COMMIT_SHORT}"
                    echo "🎯 ENVIRONMENT: ${params.ENVIRONMENT}"
                    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
                }

                // Clean workspace
                cleanWs()

                // Checkout code
                checkout scm

                // Send notification
                slackSend(
                    channel: env.SLACK_CHANNEL,
                    color: '#439FE0',
                    message: "🚀 Build Started: ${APP_NAME} v${VERSION}\nBranch: ${GIT_BRANCH}\nTriggered by: ${currentBuild.getBuildCauses()[0].shortDescription}"
                )
            }
        }

        // =====================================================================
        // STAGE 2: CODE QUALITY & SECURITY
        // =====================================================================
        stage('🔒 Code Quality & Security') {
            parallel {
                stage('Backend: Python Linting') {
                    steps {
                        script {
                            echo "🐍 Running Python linters..."
                            sh '''
                                python3 -m venv venv
                                . venv/bin/activate
                                pip install -q flake8 black mypy bandit safety

                                # Linting
                                flake8 src/ --max-line-length=120 --exclude=venv,migrations

                                # Formatting check
                                black --check src/

                                # Type checking
                                mypy src/ --ignore-missing-imports
                            '''
                        }
                    }
                }

                stage('Frontend: ESLint & Prettier') {
                    steps {
                        dir('frontend') {
                            script {
                                echo "⚛️ Running frontend linters..."
                                sh '''
                                    npm install -g pnpm
                                    pnpm install --frozen-lockfile
                                    pnpm lint
                                    pnpm format:check
                                    pnpm type-check
                                '''
                            }
                        }
                    }
                }

                stage('Security: Dependency Check') {
                    steps {
                        script {
                            echo "🛡️ Running security scans..."
                            sh '''
                                # Backend: Safety check
                                . venv/bin/activate
                                safety check --file requirements.txt || true

                                # Backend: Bandit (Python security)
                                bandit -r src/ -ll || true

                                # Frontend: npm audit
                                cd frontend
                                pnpm audit --audit-level=moderate || true
                            '''
                        }
                    }
                }

                stage('Security: Trivy Scan') {
                    steps {
                        script {
                            echo "🔐 Scanning for vulnerabilities with Trivy..."
                            sh '''
                                # Install Trivy if not present
                                if ! command -v trivy &> /dev/null; then
                                    wget -qO - https://aquasecurity.github.io/trivy-repo/deb/public.key | sudo apt-key add -
                                    echo "deb https://aquasecurity.github.io/trivy-repo/deb $(lsb_release -sc) main" | sudo tee -a /etc/apt/sources.list.d/trivy.list
                                    sudo apt-get update
                                    sudo apt-get install -y trivy
                                fi

                                # Scan filesystem
                                trivy fs --severity HIGH,CRITICAL . || true
                            '''
                        }
                    }
                }
            }
        }

        // =====================================================================
        // STAGE 3: TESTING
        // =====================================================================
        stage('🧪 Testing') {
            when {
                expression { !params.SKIP_TESTS }
            }
            parallel {
                stage('Backend: Unit Tests') {
                    steps {
                        script {
                            echo "🧪 Running backend unit tests..."
                            sh '''
                                . venv/bin/activate
                                pip install -q -r requirements.txt

                                # Run tests with coverage
                                pytest tests/unit/ -v \
                                    --cov=src \
                                    --cov-report=xml \
                                    --cov-report=html \
                                    --cov-report=term-missing \
                                    --junit-xml=test-results/backend-unit.xml
                            '''
                        }
                    }
                    post {
                        always {
                            junit 'test-results/backend-unit.xml'
                            publishHTML([
                                reportDir: 'htmlcov',
                                reportFiles: 'index.html',
                                reportName: 'Backend Coverage Report'
                            ])
                        }
                    }
                }

                stage('Backend: Integration Tests') {
                    steps {
                        script {
                            echo "🔗 Running backend integration tests..."
                            sh '''
                                . venv/bin/activate

                                # Start test database
                                docker-compose -f docker-compose.test.yml up -d postgres redis

                                # Wait for services
                                sleep 10

                                # Run integration tests
                                pytest tests/integration/ -v \
                                    --junit-xml=test-results/backend-integration.xml

                                # Cleanup
                                docker-compose -f docker-compose.test.yml down -v
                            '''
                        }
                    }
                    post {
                        always {
                            junit 'test-results/backend-integration.xml'
                        }
                    }
                }

                stage('Frontend: Unit Tests') {
                    steps {
                        dir('frontend') {
                            script {
                                echo "⚛️ Running frontend unit tests..."
                                sh '''
                                    pnpm test:coverage -- --reporter=junit --outputFile=test-results/frontend-unit.xml
                                '''
                            }
                        }
                    }
                    post {
                        always {
                            junit 'frontend/test-results/frontend-unit.xml'
                            publishHTML([
                                reportDir: 'frontend/coverage',
                                reportFiles: 'index.html',
                                reportName: 'Frontend Coverage Report'
                            ])
                        }
                    }
                }

                stage('Frontend: E2E Tests (Playwright)') {
                    steps {
                        dir('frontend') {
                            script {
                                echo "🎭 Running E2E tests with Playwright..."
                                sh '''
                                    # Install Playwright browsers
                                    pnpm exec playwright install --with-deps chromium

                                    # Start dev server in background
                                    pnpm dev &
                                    DEV_PID=$!

                                    # Wait for server to be ready
                                    sleep 30

                                    # Run E2E tests
                                    pnpm test:e2e || E2E_FAILED=true

                                    # Kill dev server
                                    kill $DEV_PID

                                    # Fail if tests failed
                                    [ "$E2E_FAILED" = true ] && exit 1 || exit 0
                                '''
                            }
                        }
                    }
                    post {
                        always {
                            publishHTML([
                                reportDir: 'frontend/playwright-report',
                                reportFiles: 'index.html',
                                reportName: 'Playwright E2E Report'
                            ])
                        }
                    }
                }
            }
        }

        // =====================================================================
        // STAGE 4: BUILD DOCKER IMAGES
        // =====================================================================
        stage('🐳 Build Docker Images') {
            parallel {
                stage('Backend Image') {
                    steps {
                        script {
                            echo "🔨 Building backend Docker image..."
                            sh """
                                docker buildx build \
                                    --platform linux/amd64,linux/arm64 \
                                    --tag ${DOCKER_REGISTRY}/backend:${VERSION} \
                                    --tag ${DOCKER_REGISTRY}/backend:latest \
                                    --build-arg PYTHON_VERSION=3.11 \
                                    --cache-from ${DOCKER_REGISTRY}/backend:latest \
                                    --push \
                                    -f Dockerfile \
                                    .
                            """
                        }
                    }
                }

                stage('Frontend Image') {
                    steps {
                        dir('frontend') {
                            script {
                                echo "🔨 Building frontend Docker image..."
                                sh """
                                    docker buildx build \
                                        --platform linux/amd64,linux/arm64 \
                                        --tag ${DOCKER_REGISTRY}/frontend:${VERSION} \
                                        --tag ${DOCKER_REGISTRY}/frontend:latest \
                                        --cache-from ${DOCKER_REGISTRY}/frontend:latest \
                                        --push \
                                        -f Dockerfile \
                                        .
                                """
                            }
                        }
                    }
                }
            }
        }

        // =====================================================================
        // STAGE 5: SECURITY SCANNING (Post-build)
        // =====================================================================
        stage('🔐 Container Security Scan') {
            parallel {
                stage('Scan Backend Image') {
                    steps {
                        script {
                            echo "🔍 Scanning backend image with Trivy..."
                            sh """
                                trivy image \
                                    --severity HIGH,CRITICAL \
                                    --exit-code 0 \
                                    ${DOCKER_REGISTRY}/backend:${VERSION}
                            """
                        }
                    }
                }

                stage('Scan Frontend Image') {
                    steps {
                        script {
                            echo "🔍 Scanning frontend image with Trivy..."
                            sh """
                                trivy image \
                                    --severity HIGH,CRITICAL \
                                    --exit-code 0 \
                                    ${DOCKER_REGISTRY}/frontend:${VERSION}
                            """
                        }
                    }
                }
            }
        }

        // =====================================================================
        // STAGE 6: DATABASE MIGRATIONS
        // =====================================================================
        stage('🗄️ Database Migrations') {
            when {
                expression { params.ENVIRONMENT == 'staging' || params.ENVIRONMENT == 'production' }
            }
            steps {
                script {
                    echo "📊 Running database migrations..."
                    sh '''
                        # Backup database first
                        ./deployment/scripts/backup-database.sh

                        # Dry-run migration
                        docker-compose exec -T fastapi alembic upgrade head --sql > migration-preview.sql

                        echo "Migration Preview:"
                        cat migration-preview.sql

                        # Apply migration
                        docker-compose exec -T fastapi alembic upgrade head
                    '''
                }
            }
        }

        // =====================================================================
        // STAGE 7: DEPLOY TO KUBERNETES
        // =====================================================================
        stage('☸️ Deploy to Kubernetes') {
            when {
                expression { params.ENVIRONMENT == 'staging' || params.ENVIRONMENT == 'production' }
            }
            steps {
                script {
                    echo "🚀 Deploying to Kubernetes (${params.ENVIRONMENT})..."

                    // Update Kubernetes manifests with new image tags
                    sh """
                        # Update backend deployment
                        kubectl set image deployment/backend-deployment \
                            backend=${DOCKER_REGISTRY}/backend:${VERSION} \
                            --namespace=${K8S_NAMESPACE} \
                            --record

                        # Update frontend deployment
                        kubectl set image deployment/frontend-deployment \
                            frontend=${DOCKER_REGISTRY}/frontend:${VERSION} \
                            --namespace=${K8S_NAMESPACE} \
                            --record

                        # Wait for rollout to complete
                        kubectl rollout status deployment/backend-deployment --namespace=${K8S_NAMESPACE} --timeout=10m
                        kubectl rollout status deployment/frontend-deployment --namespace=${K8S_NAMESPACE} --timeout=10m
                    """
                }
            }
        }

        // =====================================================================
        // STAGE 8: SMOKE TESTS (Post-deployment)
        // =====================================================================
        stage('💨 Smoke Tests') {
            when {
                expression { params.ENVIRONMENT == 'staging' || params.ENVIRONMENT == 'production' }
            }
            steps {
                script {
                    echo "🔥 Running smoke tests..."
                    sh '''
                        # Get service URLs
                        BACKEND_URL=$(kubectl get svc backend-service -n ${K8S_NAMESPACE} -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
                        FRONTEND_URL=$(kubectl get svc frontend-service -n ${K8S_NAMESPACE} -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

                        # Test backend health
                        curl -f http://${BACKEND_URL}:8000/health || exit 1

                        # Test frontend health
                        curl -f http://${FRONTEND_URL}:3000 || exit 1

                        # Test API endpoint
                        curl -f http://${BACKEND_URL}:8000/api/health || exit 1

                        echo "✅ All smoke tests passed!"
                    '''
                }
            }
        }
    }

    // =========================================================================
    // POST-BUILD ACTIONS
    // =========================================================================
    post {
        success {
            script {
                slackSend(
                    channel: env.SLACK_CHANNEL,
                    color: 'good',
                    message: """
✅ *BUILD SUCCESS*
📦 ${APP_NAME} v${VERSION}
🌿 Branch: ${GIT_BRANCH}
⏱️ Duration: ${currentBuild.durationString}
🎯 Environment: ${params.ENVIRONMENT}
🔗 ${env.BUILD_URL}
                    """
                )
            }
        }

        failure {
            script {
                slackSend(
                    channel: env.SLACK_CHANNEL,
                    color: 'danger',
                    message: """
❌ *BUILD FAILED*
📦 ${APP_NAME} v${VERSION}
🌿 Branch: ${GIT_BRANCH}
⏱️ Duration: ${currentBuild.durationString}
🔗 ${env.BUILD_URL}console
                    """
                )
            }
        }

        unstable {
            script {
                slackSend(
                    channel: env.SLACK_CHANNEL,
                    color: 'warning',
                    message: """
⚠️ *BUILD UNSTABLE*
📦 ${APP_NAME} v${VERSION}
🌿 Branch: ${GIT_BRANCH}
🔗 ${env.BUILD_URL}
                    """
                )
            }
        }

        always {
            // Clean up workspace
            cleanWs()

            // Archive artifacts
            archiveArtifacts artifacts: 'test-results/**/*.xml', allowEmptyArchive: true

            // Publish test results
            junit testResults: 'test-results/**/*.xml', allowEmptyResults: true
        }
    }
}
