pyinstaller --clean tuition_generator.spec

cp ./dist/TuitionGenerator ~/.local/bin/

echo "Built Complete!"