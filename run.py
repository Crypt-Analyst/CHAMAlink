from app import create_app

app = create_app()

# Health check route for deployment
@app.route('/health')
def health_check():
    return {'status': 'healthy', 'service': 'chamalink'}

if __name__ == '__main__':
    app.run(debug=True)
