#!/bin/bash
# Deploy Sharedo DOCX to HTML Converter to Azure Container Apps
# Usage: ./scripts/deploy.sh <environment> [options]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
ENVIRONMENT=${1:-dev}
RESOURCE_GROUP=${RESOURCE_GROUP:-Docspective}
ACR_NAME=${ACR_NAME:-docspectiveacr}
APP_NAME=${APP_NAME:-sharedo-docx-converter}
LOCATION=${LOCATION:-australiaeast}

# Function to print colored output
print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Function to check prerequisites
check_prerequisites() {
    print_message "$YELLOW" "Checking prerequisites..."
    
    # Check if Azure CLI is installed
    if ! command -v az &> /dev/null; then
        print_message "$RED" "Azure CLI is not installed. Please install it first."
        exit 1
    fi
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        print_message "$RED" "Docker is not installed. Please install it first."
        exit 1
    fi
    
    # Check if logged in to Azure
    if ! az account show &> /dev/null; then
        print_message "$RED" "Not logged in to Azure. Please run 'az login' first."
        exit 1
    fi
    
    print_message "$GREEN" "Prerequisites check passed!"
}

# Function to build Docker image
build_image() {
    print_message "$YELLOW" "Building Docker image..."
    
    IMAGE_TAG="${ACR_NAME}.azurecr.io/${APP_NAME}:${ENVIRONMENT}-$(git rev-parse --short HEAD 2>/dev/null || echo 'latest')"
    
    docker build \
        -t "${IMAGE_TAG}" \
        -f Dockerfile \
        .
    
    print_message "$GREEN" "Docker image built: ${IMAGE_TAG}"
    echo "${IMAGE_TAG}"
}

# Function to push image to ACR
push_image() {
    local image_tag=$1
    
    print_message "$YELLOW" "Pushing image to Azure Container Registry..."
    
    # Login to ACR
    az acr login --name "${ACR_NAME}"
    
    # Push image
    docker push "${image_tag}"
    
    print_message "$GREEN" "Image pushed successfully!"
}

# Function to deploy with Bicep
deploy_bicep() {
    local image_tag=$1
    
    print_message "$YELLOW" "Deploying to Azure Container Apps using Bicep..."
    
    # Set parameter file based on environment
    PARAMETER_FILE="azure/parameters-${ENVIRONMENT}.json"
    
    if [ ! -f "$PARAMETER_FILE" ]; then
        print_message "$RED" "Parameter file not found: ${PARAMETER_FILE}"
        exit 1
    fi
    
    # Deploy using Bicep
    DEPLOYMENT_NAME="${APP_NAME}-${ENVIRONMENT}-$(date +%Y%m%d%H%M%S)"
    
    az deployment group create \
        --resource-group "${RESOURCE_GROUP}" \
        --template-file azure/main.bicep \
        --parameters "@${PARAMETER_FILE}" \
        --parameters containerImage="${image_tag}" \
        --name "${DEPLOYMENT_NAME}" \
        --output table
    
    # Get deployment outputs
    APP_URL=$(az deployment group show \
        --resource-group "${RESOURCE_GROUP}" \
        --name "${DEPLOYMENT_NAME}" \
        --query properties.outputs.containerAppUrl.value \
        --output tsv)
    
    print_message "$GREEN" "Deployment completed successfully!"
    print_message "$GREEN" "Application URL: ${APP_URL}"
}

# Function to validate deployment
validate_deployment() {
    local app_url=$1
    
    print_message "$YELLOW" "Validating deployment..."
    
    # Wait for app to be ready
    sleep 30
    
    # Check health endpoint
    HEALTH_URL="${app_url}/health"
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "${HEALTH_URL}")
    
    if [ "$HTTP_CODE" == "200" ]; then
        print_message "$GREEN" "Health check passed! Application is running."
        
        # Get health status
        curl -s "${HEALTH_URL}" | python3 -m json.tool
    else
        print_message "$RED" "Health check failed. HTTP Code: ${HTTP_CODE}"
        exit 1
    fi
}

# Function to display deployment summary
display_summary() {
    local app_url=$1
    
    print_message "$GREEN" "\n=========================================="
    print_message "$GREEN" "Deployment Summary"
    print_message "$GREEN" "=========================================="
    echo "Environment: ${ENVIRONMENT}"
    echo "Resource Group: ${RESOURCE_GROUP}"
    echo "ACR: ${ACR_NAME}"
    echo "Application: ${APP_NAME}"
    echo "Location: ${LOCATION}"
    echo ""
    echo "URLs:"
    echo "- Application: ${app_url}"
    echo "- Swagger Docs: ${app_url}/docs"
    echo "- Health Check: ${app_url}/health"
    echo "- Metrics: ${app_url}/metrics"
    print_message "$GREEN" "=========================================="
}

# Main execution
main() {
    print_message "$GREEN" "Starting deployment of Sharedo DOCX to HTML Converter"
    print_message "$YELLOW" "Environment: ${ENVIRONMENT}"
    
    # Check prerequisites
    check_prerequisites
    
    # Build Docker image
    IMAGE_TAG=$(build_image)
    
    # Push to ACR
    push_image "${IMAGE_TAG}"
    
    # Deploy with Bicep
    deploy_bicep "${IMAGE_TAG}"
    
    # Get app URL from deployment
    APP_URL=$(az deployment group show \
        --resource-group "${RESOURCE_GROUP}" \
        --name "${DEPLOYMENT_NAME}" \
        --query properties.outputs.containerAppUrl.value \
        --output tsv)
    
    # Validate deployment
    validate_deployment "${APP_URL}"
    
    # Display summary
    display_summary "${APP_URL}"
}

# Run main function
main