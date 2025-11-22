import React, { useState } from 'react';
import {
    Modal,
    StyleSheet,
    Text,
    TextInput,
    TouchableOpacity,
    View,
    KeyboardAvoidingView,
    Platform,
} from 'react-native';

type AddInventoryModalProps = {
    visible: boolean;
    onClose: () => void;
    onAdd: (item: { name: string; quantity: number; unit?: string; expires_on?: string }) => Promise<void>;
};

export function AddInventoryModal({ visible, onClose, onAdd }: AddInventoryModalProps) {
    const [name, setName] = useState('');
    const [quantity, setQuantity] = useState('');
    const [unit, setUnit] = useState('');
    const [expiresOn, setExpiresOn] = useState('');
    const [loading, setLoading] = useState(false);

    const handleAdd = async () => {
        if (!name || !quantity) {
            return;
        }

        setLoading(true);
        try {
            await onAdd({
                name,
                quantity: parseFloat(quantity),
                unit: unit || undefined,
                expires_on: expiresOn || undefined,
            });
            setName('');
            setQuantity('');
            setUnit('');
            setExpiresOn('');
            onClose();
        } catch (error) {
            console.error('Failed to add item:', error);
        } finally {
            setLoading(false);
        }
    };

    return (
        <Modal visible={visible} animationType="slide" transparent>
            <KeyboardAvoidingView
                behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
                style={styles.modalContainer}
            >
                <View style={styles.modalContent}>
                    <Text style={styles.title}>Add Food</Text>

                    <TextInput
                        style={styles.input}
                        placeholder="Name (e.g. Apple)"
                        value={name}
                        onChangeText={setName}
                        autoFocus
                    />

                    <View style={styles.row}>
                        <TextInput
                            style={[styles.input, styles.halfInput]}
                            placeholder="Quantity"
                            value={quantity}
                            onChangeText={setQuantity}
                            keyboardType="numeric"
                        />
                        <TextInput
                            style={[styles.input, styles.halfInput]}
                            placeholder="Unit (optional)"
                            value={unit}
                            onChangeText={setUnit}
                        />
                    </View>

                    <TextInput
                        style={styles.input}
                        placeholder="Expires On (YYYY-MM-DD, optional)"
                        value={expiresOn}
                        onChangeText={setExpiresOn}
                    />

                    <View style={styles.buttonRow}>
                        <TouchableOpacity style={[styles.button, styles.cancelButton]} onPress={onClose}>
                            <Text style={styles.buttonText}>Cancel</Text>
                        </TouchableOpacity>
                        <TouchableOpacity
                            style={[styles.button, styles.addButton, loading && styles.disabledButton]}
                            onPress={handleAdd}
                            disabled={loading}
                        >
                            <Text style={[styles.buttonText, styles.addButtonText]}>
                                {loading ? 'Adding...' : 'Add'}
                            </Text>
                        </TouchableOpacity>
                    </View>
                </View>
            </KeyboardAvoidingView>
        </Modal>
    );
}

const styles = StyleSheet.create({
    modalContainer: {
        flex: 1,
        justifyContent: 'flex-end',
        backgroundColor: 'rgba(0, 0, 0, 0.5)',
    },
    modalContent: {
        backgroundColor: 'white',
        borderTopLeftRadius: 20,
        borderTopRightRadius: 20,
        padding: 20,
        paddingBottom: 40,
    },
    title: {
        fontSize: 20,
        fontWeight: 'bold',
        marginBottom: 20,
        textAlign: 'center',
    },
    input: {
        borderWidth: 1,
        borderColor: '#ddd',
        borderRadius: 8,
        padding: 12,
        marginBottom: 16,
        fontSize: 16,
    },
    row: {
        flexDirection: 'row',
        justifyContent: 'space-between',
    },
    halfInput: {
        width: '48%',
    },
    buttonRow: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        marginTop: 10,
    },
    button: {
        flex: 1,
        padding: 16,
        borderRadius: 8,
        alignItems: 'center',
    },
    cancelButton: {
        backgroundColor: '#f0f0f0',
        marginRight: 10,
    },
    addButton: {
        backgroundColor: '#007AFF',
        marginLeft: 10,
    },
    disabledButton: {
        opacity: 0.7,
    },
    buttonText: {
        fontSize: 16,
        fontWeight: '600',
    },
    addButtonText: {
        color: 'white',
    },
});
