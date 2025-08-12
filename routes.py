from flask import Blueprint, request, jsonify
from services import (
    add_customer,
    update_due,
    delete_customer,
    get_all_customers
)
from decorators import log_action

routes = Blueprint('routes', __name__)

@routes.route('/customers', methods=['GET'])
@log_action("Fetching all customers")
def api_get_customers():
    """Get list of all customers"""
    try:
        customers = get_all_customers()
        return jsonify(customers)
    except Exception as e:
        return jsonify({"error": f"Failed to fetch customers: {str(e)}"}), 500


@routes.route('/customer', methods=['POST'])
@log_action("Adding new customer via API")
def api_add_customer():
    """Add a new customer"""
    data = request.json or {}
    name = data.get('name')
    phone = data.get('phone')
    address = data.get('address', '')
    due = data.get('due', 0.0)
    category = data.get('category', 'Regular')

    if not name or not phone:
        return jsonify({"error": "Name and phone are required"}), 400

    if not str(phone).isdigit() or len(str(phone)) != 10:
        return jsonify({"error": "Invalid phone number format. Must be exactly 10 digits."}), 400

    try:
        new_customer = add_customer(name, phone, address, due, category)
        return jsonify(new_customer), 201
    except Exception as e:
        return jsonify({"error": f"Failed to add customer: {str(e)}"}), 500


@routes.route('/customer/<int:customer_id>/due', methods=['PUT'])
@log_action("Updating due amount via API")
def api_update_due(customer_id):
    """Update due amount for a customer"""
    data = request.json or {}
    new_due = data.get('due')

    if new_due is None:
        return jsonify({"error": "Due amount is required"}), 400

    try:
        updated_customer = update_due(customer_id, new_due)
        if not updated_customer:
            return jsonify({"error": "Customer not found"}), 404
        return jsonify(updated_customer)
    except Exception as e:
        return jsonify({"error": f"Failed to update due: {str(e)}"}), 500


@routes.route('/customer/<int:customer_id>', methods=['DELETE'])
@log_action("Deleting customer via API")
def api_delete_customer(customer_id):
    """Delete a customer by ID"""
    try:
        success = delete_customer(customer_id)
        if not success:
            return jsonify({"error": "Customer not found"}), 404
        return jsonify({"message": "Customer deleted successfully"}), 200
    except Exception as e:
        return jsonify({"error": f"Failed to delete customer: {str(e)}"}), 500

@routes.route('/customers', methods=['DELETE'])
def api_delete_all_customers():
    """Delete all customers"""
    success = delete_all_customers()
    if not success:
        return jsonify({"error": "No customers to delete"}), 404
    return jsonify({"message": "All customers deleted successfully"}), 200
