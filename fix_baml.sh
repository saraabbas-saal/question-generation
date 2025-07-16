#!/bin/bash

echo "🔧 Fixing BAML Client Generation..."

# Step 1: Check if BAML CLI is installed
echo "1️⃣ Checking BAML CLI installation..."
if ! command -v baml-cli &> /dev/null; then
    echo "❌ BAML CLI not found. Installing..."
    pip install baml-cli
else
    echo "✅ BAML CLI found"
fi

# Step 2: Check BAML source files
echo -e "\n2️⃣ Checking BAML source files..."
if [ -d "baml_src" ]; then
    echo "✅ baml_src directory found"
    ls -la baml_src/
else
    echo "❌ baml_src directory not found!"
    exit 1
fi

# Step 3: Clean old generated files
echo -e "\n3️⃣ Cleaning old generated files..."
if [ -d "baml_client" ]; then
    echo "🗑️ Removing old baml_client directory..."
    rm -rf baml_client
fi

# Step 4: Generate BAML client
echo -e "\n4️⃣ Generating BAML client..."
baml-cli generate

# Step 5: Verify generation
echo -e "\n5️⃣ Verifying BAML client generation..."
if [ -d "baml_client" ]; then
    echo "✅ baml_client directory created"
    
    if [ -f "baml_client/__init__.py" ]; then
        echo "✅ __init__.py found"
        
        # Check if 'b' is exported
        if grep -q "b" baml_client/__init__.py; then
            echo "✅ 'b' client found in __init__.py"
        else
            echo "❌ 'b' client not found in __init__.py"
            echo "Contents of __init__.py:"
            cat baml_client/__init__.py
        fi
    else
        echo "❌ __init__.py not found"
    fi
    
    echo -e "\nGenerated files:"
    ls -la baml_client/
else
    echo "❌ baml_client directory not created"
    exit 1
fi

echo -e "\n✅ BAML client generation complete!"