yes | pyinstaller --clean tuition_generator.spec

cp -f ./dist/TuitionGenerator ~/.local/bin/

echo "Built Complete!"