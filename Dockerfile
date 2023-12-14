# Use the Jupyter Data Science Notebook as a base image
FROM quay.io/jupyter/datascience-notebook

# Set a maintainer label: replace with your name and email
LABEL maintainer="your.name@example.com"

# Install additional packages or perform customizations below
# For example, to install additional Python packages:
# RUN pip install package-name1 package-name2

# Any additional customizations, environment variables, etc.
# ENV MY_ENVIRONMENT_VAR=my_value

# Copy the notebook directory into the image
COPY . /notebooks

# Set the working directory to the notebooks directory
WORKDIR /notebooks

# The container listens on port 8888 by default for Jupyter Notebook
EXPOSE 8888

# Run Jupyter Notebook (this is usually already defined in the base image)
# CMD ["start-notebook.sh"]
