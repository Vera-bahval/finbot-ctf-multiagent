from flask import Blueprint, request, jsonify
import json
import openai
from src.models.vendor import db, Vendor, Invoice
# Импортируем новую мультиагентную систему
from src.services.multi_agent_finbot import MultiAgentFinBot
from datetime import datetime

vendor_bp = Blueprint('vendor', __name__)


@vendor_bp.route('/vendors', methods=['POST'])
def register_vendor():
    """Register a new vendor"""
    try:
        data = request.get_json()
        
        existing_vendor = Vendor.query.filter_by(contact_email=data['contact_email']).first()
        if existing_vendor:
            return jsonify({"error": "Vendor with this email already exists"}), 400
        
        vendor = Vendor(
            company_name=data['company_name'],
            contact_person=data['contact_person'],
            contact_email=data['contact_email'],
            phone_number=data['phone_number'],
            business_type=data['business_type'],
            vendor_category=json.dumps(data.get('vendor_category', [])),
            tax_id=data['tax_id'],
            bank_name=data['bank_name'],
            account_holder_name=data['account_holder_name'],
            account_number=data['account_number'],
            routing_number=data['routing_number'],
            services_description=data.get('services_description', ''),
            status='approved',
            trust_level='standard'
        )
        
        db.session.add(vendor)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "vendor_id": vendor.id,
            "message": "Vendor registered successfully"
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@vendor_bp.route('/vendors/<int:vendor_id>', methods=['GET'])
def get_vendor(vendor_id):
    """Get vendor details"""
    vendor = Vendor.query.get(vendor_id)
    if not vendor:
        return jsonify({"error": "Vendor not found"}), 404
    
    return jsonify(vendor.to_dict())

@vendor_bp.route('/vendors', methods=['GET'])
def list_vendors():
    """List all vendors"""
    vendors = Vendor.query.all()
    return jsonify([vendor.to_dict() for vendor in vendors])

@vendor_bp.route('/vendors/<int:vendor_id>/invoices', methods=['POST'])
def submit_invoice(vendor_id):
    """Submit an invoice for processing - ТЕПЕРЬ ИСПОЛЬЗУЕТ МУЛЬТИАГЕНТНУЮ СИСТЕМУ"""
    try:
        vendor = Vendor.query.get(vendor_id)
        if not vendor:
            return jsonify({"error": "Vendor not found"}), 404
        
        data = request.get_json()
        
        existing_invoice = Invoice.query.filter_by(invoice_number=data['invoice_number']).first()
        if existing_invoice:
            return jsonify({"error": "Invoice number already exists"}), 400
        
        invoice_date = datetime.strptime(data['invoice_date'], '%Y-%m-%d').date()
        due_date = datetime.strptime(data['due_date'], '%Y-%m-%d').date()
        
        invoice = Invoice(
            vendor_id=vendor_id,
            invoice_number=data['invoice_number'],
            amount=float(data['amount']),
            description=data['description'],
            invoice_date=invoice_date,
            due_date=due_date,
            status='submitted'
        )
        
        db.session.add(invoice)
        db.session.commit()
        
        # ОБРАБОТКА ЧЕРЕЗ МУЛЬТИАГЕНТНУЮ СИСТЕМУ
        print(f"\n{'='*60}")
        print(f"MULTI-AGENT PROCESSING: Invoice #{invoice.id}")
        print(f"{'='*60}")
        
        try:
            # Создаем экземпляр внутри функции (внутри контекста Flask)
            multi_agent_finbot = MultiAgentFinBot()
            result = multi_agent_finbot.process_invoice(invoice.id)
            
            print(f"\n{'='*60}")
            print(f"PROCESSING COMPLETE")
            print(f"Result keys: {list(result.keys())}")
            print(f"Final Decision: {result.get('final_decision', 'UNKNOWN')}")
            if 'cascade_analysis' in result:
                print(f"Cascade Failures: {result['cascade_analysis'].get('cascade_failures_detected', 'UNKNOWN')}")
                print(f"Confidence Degradation: {result['cascade_analysis'].get('confidence_degradation', 0):.3f}")
            else:
                print("⚠️  NO CASCADE ANALYSIS IN RESULT")
            print(f"{'='*60}\n")
            
            return jsonify({
                "success": True,
                "invoice_id": invoice.id,
                "processing_result": result
            }), 201
            
        except Exception as e:
            print(f"\n❌ EXCEPTION IN PROCESSING: {e}")
            import traceback
            traceback.print_exc()
            db.session.rollback()
            return jsonify({"error": f"Processing failed: {str(e)}"}), 500
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
    
@vendor_bp.route('/vendors/<int:vendor_id>/invoices/test_validator', methods=['POST'])
def submit_invoice_validator(vendor_id):
    """Submit an invoice for processing - ТЕПЕРЬ ИСПОЛЬЗУЕТ МУЛЬТИАГЕНТНУЮ СИСТЕМУ"""
    try:
        vendor = Vendor.query.get(vendor_id)
        if not vendor:
            return jsonify({"error": "Vendor not found"}), 404
        
        data = request.get_json()
        
        existing_invoice = Invoice.query.filter_by(invoice_number=data['invoice_number']).first()
        if existing_invoice:
            return jsonify({"error": "Invoice number already exists"}), 400
        
        invoice_date = datetime.strptime(data['invoice_date'], '%Y-%m-%d').date()
        due_date = datetime.strptime(data['due_date'], '%Y-%m-%d').date()
        
        invoice = Invoice(
            vendor_id=vendor_id,
            invoice_number=data['invoice_number'],
            amount=float(data['amount']),
            description=data['description'],
            invoice_date=invoice_date,
            due_date=due_date,
            status='submitted'
        )
        
        db.session.add(invoice)
        db.session.commit()
        
        # ОБРАБОТКА ЧЕРЕЗ МУЛЬТИАГЕНТНУЮ СИСТЕМУ
        print(f"\n{'='*60}")
        print(f"MULTI-AGENT PROCESSING: Invoice #{invoice.id}")
        print(f"{'='*60}")
        
        try:
            # Создаем экземпляр внутри функции (внутри контекста Flask)
            multi_agent_finbot = MultiAgentFinBot()
            result = multi_agent_finbot.test_validator_invoice(invoice.id)
            
            print(f"\n{'='*60}")
            print(f"PROCESSING COMPLETE")
            for key, value in result.items():
                print(f"{key}: {value}")
            print(f"{'='*60}\n")
            
            return jsonify({
                "message": "Invoice processed",
                "invoice_id": invoice.id,
                "validation_result": result
            }), 201
        
        except Exception as e:
            print(f"\n❌ EXCEPTION IN PROCESSING: {e}")
            import traceback
            traceback.print_exc()
            db.session.rollback()
            return jsonify({"error": f"Processing failed: {str(e)}"}), 500
        
    except openai.APIError as e:
        print(f"OpenAI API Error: {e}")
        db.session.rollback()
        return jsonify({"error": f"AI service unavailable: {str(e)}"}), 503
    
    except Exception as e:
        print(f"Server error: {e}")
        import traceback
        traceback.print_exc()
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@vendor_bp.route('/vendors/<int:vendor_id>/invoices', methods=['GET'])
def get_vendor_invoices(vendor_id):
    """Get all invoices for a vendor"""
    vendor = Vendor.query.get(vendor_id)
    if not vendor:
        return jsonify({"error": "Vendor not found"}), 404
    
    invoices = Invoice.query.filter_by(vendor_id=vendor_id).order_by(Invoice.created_at.desc()).all()
    return jsonify([invoice.to_dict() for invoice in invoices])

@vendor_bp.route('/invoices/<int:invoice_id>', methods=['GET'])
def get_invoice(invoice_id):
    """Get invoice details with cascade analysis"""
    invoice = Invoice.query.get(invoice_id)
    if not invoice:
        return jsonify({"error": "Invoice not found"}), 404
    
    invoice_data = invoice.to_dict()
    vendor_data = Vendor.query.get(invoice.vendor_id).to_dict()
    
    # Парсим cascade analysis если есть
    if invoice.ai_reasoning:
        try:
            reasoning_data = json.loads(invoice.ai_reasoning)
            invoice_data['cascade_analysis'] = reasoning_data.get('cascade_analysis')
            invoice_data['agent_chain'] = reasoning_data.get('agent_chain')
        except:
            pass
    
    return jsonify({
        "invoice": invoice_data,
        "vendor": vendor_data
    })

@vendor_bp.route('/invoices', methods=['GET'])
def list_invoices():
    """List all invoices with optional filtering"""
    status = request.args.get('status')
    vendor_id = request.args.get('vendor_id')
    
    query = Invoice.query
    
    if status:
        query = query.filter_by(status=status)
    if vendor_id:
        query = query.filter_by(vendor_id=vendor_id)
    
    invoices = query.order_by(Invoice.created_at.desc()).all()
    
    result = []
    for invoice in invoices:
        invoice_data = invoice.to_dict()
        vendor = Vendor.query.get(invoice.vendor_id)
        invoice_data['vendor_name'] = vendor.company_name if vendor else 'Unknown'
        
        # Добавляем информацию о каскадных ошибках
        if invoice.ai_reasoning:
            try:
                reasoning_data = json.loads(invoice.ai_reasoning)
                cascade_info = reasoning_data.get('cascade_analysis', {})
                invoice_data['cascade_failures'] = cascade_info.get('cascade_failures_detected', False)
                invoice_data['failed_agents'] = cascade_info.get('failed_agents', 0)
            except:
                pass
        
        result.append(invoice_data)
    
    return jsonify(result)

@vendor_bp.route('/invoices/<int:invoice_id>/cascade-analysis', methods=['GET'])
def get_cascade_analysis(invoice_id):
    """Получить детальный анализ каскадных ошибок для инвойса"""
    invoice = Invoice.query.get(invoice_id)
    if not invoice:
        return jsonify({"error": "Invoice not found"}), 404
    
    if not invoice.ai_reasoning:
        return jsonify({"error": "No cascade analysis available"}), 404
    
    try:
        reasoning_data = json.loads(invoice.ai_reasoning)
        
        return jsonify({
            "invoice_id": invoice_id,
            "agent_chain": reasoning_data.get('agent_chain', []),
            "cascade_analysis": reasoning_data.get('cascade_analysis', {}),
            "visualization": {
                "agents": [
                    {
                        "name": step['agent'],
                        "success": step['success'],
                        "confidence": step['confidence'],
                        "errors": step['errors']
                    }
                    for step in reasoning_data.get('agent_chain', [])
                ]
            }
        })
    except Exception as e:
        return jsonify({"error": f"Failed to parse cascade analysis: {str(e)}"}), 500