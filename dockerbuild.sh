export DOCKER_CLI_EXPERIMENTAL=enabled
docker run --rm --privileged docker/binfmt:66f9012c56a8316f9244ffd7622d7c21c1f6f28d
docker buildx create --use --name mybuilder
docker buildx inspect mybuilder --bootstrap
docker buildx build -t yyyzyyyz/fcircle --platform=linux/arm,linux/arm64,linux/amd64 . --push