#!/bin/bash
#
# Docker-based test runner for AgentGuard
# Provides safe environment for testing dangerous command handling
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

show_help() {
    echo "AgentGuard Docker Test Runner"
    echo ""
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  integration   Run integration tests in Docker (default)"
    echo "  all           Run all tests (unit + integration)"
    echo "  smoke         Run quick smoke test"
    echo "  shell         Open interactive shell in test container"
    echo "  build         Build test container only"
    echo "  clean         Remove test containers and images"
    echo "  help          Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                    # Run integration tests"
    echo "  $0 smoke              # Quick smoke test"
    echo "  $0 shell              # Interactive debugging"
    echo ""
}

build_container() {
    print_header "Building test container..."
    docker compose -f docker-compose.test.yml build
}

run_integration() {
    print_header "Running integration tests in Docker..."
    docker compose -f docker-compose.test.yml run --rm test
}

run_all() {
    print_header "Running all tests in Docker..."
    docker compose -f docker-compose.test.yml run --rm test-all
}

run_smoke() {
    print_header "Running smoke test..."
    docker compose -f docker-compose.test.yml run --rm smoke
}

run_shell() {
    print_header "Opening interactive shell..."
    echo -e "${YELLOW}You are now in a Docker container where you can safely test dangerous commands.${NC}"
    echo -e "${YELLOW}Try: agentguard -- rm -rf /${NC}"
    echo ""
    docker compose -f docker-compose.test.yml run --rm shell
}

clean_docker() {
    print_header "Cleaning up Docker resources..."
    docker compose -f docker-compose.test.yml down --rmi local --volumes --remove-orphans 2>/dev/null || true
    echo -e "${GREEN}Cleanup complete.${NC}"
}

# Main
case "${1:-integration}" in
    integration)
        build_container
        run_integration
        ;;
    all)
        build_container
        run_all
        ;;
    smoke)
        build_container
        run_smoke
        ;;
    shell)
        build_container
        run_shell
        ;;
    build)
        build_container
        ;;
    clean)
        clean_docker
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo -e "${RED}Unknown command: $1${NC}"
        echo ""
        show_help
        exit 1
        ;;
esac
