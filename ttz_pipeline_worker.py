import argparse

from story_pipeline import main


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--instance-name", default="story_worker1")
    args = parser.parse_args()
    main(instance_name=args.instance_name)
